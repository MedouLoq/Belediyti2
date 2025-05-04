from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.db.models import Q
from .models import User, Citizen, Problem, Complaint, Municipality, Category
from .forms import (
    CitizenRegistrationForm, ProblemReportForm, ComplaintForm,
    CitizenProfileForm, LoginForm
)
from django.http import JsonResponse
import json
import logging

logger = logging.getLogger(__name__)

try:
    from shapely.geometry import Point, shape
    SHAPELY_INSTALLED = True
except ImportError:
    SHAPELY_INSTALLED = False
    Point, shape = None, None

def get_municipality_id(request):
    name = request.GET.get("name", "").strip()
    lat = float(request.GET.get("lat", 0))
    lon = float(request.GET.get("lon", 0))

    logger.debug(f"Received municipality name: , lat: {lat}, lon: {lon}")

    if not name:
        logger.warning("No municipality name provided")
        return JsonResponse({"municipality_id": ""})

    # Log all municipalities in the database for debugging
    all_municipalities = list(Municipality.objects.all().values_list("name", flat=True))
    logger.debug(f"All municipalities in database: {all_municipalities}")

    # Try exact match (case-insensitive, after stripping whitespace)
    municipality = Municipality.objects.filter(name__iexact=name.strip()).first()
    if municipality:
        logger.debug(f"Exact match found: {municipality.name} (ID: {municipality.id})")
        return JsonResponse({"municipality_id": municipality.id})

    # Try partial match
    municipality = Municipality.objects.filter(name__icontains=name.strip()).first()
    if municipality:
        logger.debug(f"Partial match found: {municipality.name} (ID: {municipality.id})")
        return JsonResponse({"municipality_id": municipality.id})

    # Specific handling for Ksar
    if name.lower().strip() == "ksar":
        municipality = Municipality.objects.filter(name__iexact="Ksar").first()
        if municipality:
            logger.debug(f"Ksar match found: {municipality.name} (ID: {municipality.id})")
            return JsonResponse({"municipality_id": municipality.id})

    # Boundary check if shapely is available
    if SHAPELY_INSTALLED and lat and lon:
        point = Point(lon, lat)
        for mun in Municipality.objects.exclude(boundary__isnull=True).exclude(boundary=""):
            try:
                boundary = json.loads(mun.boundary)
                if boundary and shape(boundary).contains(point):
                    logger.debug(f"Boundary match found: {mun.name} (ID: {mun.id})")
                    return JsonResponse({"municipality_id": mun.id})
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Boundary error for {mun.name}: {e}")
                continue

    logger.warning(f"No municipality found for name: ")
    return JsonResponse({"municipality_id": ""})

# View for role-based redirection after login
def redirect_user(request):
    if request.user.is_authenticated:
        if request.user.user_type == "CITIZEN":
            return redirect("citizen_dashboard")
        elif request.user.user_type == "SUPERADMIN":
            # Redirect Admins/Super Admins to the Django admin index
            return redirect("superadmin:superadmin_home")
        elif request.user.user_type == "ADMIN":
            return redirect("Muni_admin:admin_home")
    # If not authenticated or unknown type, redirect to login
    return redirect("login")

def user_login(request):
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect("redirect_user") # Use the redirector view

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data.get("identifier")
            password = form.cleaned_data.get("password")

            # Authenticate using the custom backend (which handles phone or email)
            user = authenticate(request, username=identifier, password=password)

            if user is not None:
                # Check if the user is active
                if user.is_active:
                    login(request, user)
                    messages.success(request, f"Connexion réussie! Bonjour {user}.")
                    # Redirect based on role using the dedicated view
                    return redirect("redirect_user")
                else:
                    messages.error(request, "Ce compte est désactivé.")
            else:
                messages.error(request, "Numéro de téléphone/Email ou mot de passe incorrect.")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = LoginForm()

    return render(request, "citizens/login.html", {"form": form})



@login_required
def user_logout(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect("login")

def register(request):
    if request.user.is_authenticated:
        return redirect("redirect_user") # Use the redirector view

    if request.method == "POST":
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # *** FIX: Specify the backend when logging in ***
                login(request, user, backend="Citoyen.backends.PhoneOrEmailBackend")
                messages.success(request, "Compte créé et connecté!")
                return redirect("citizen_dashboard") # Redirect citizen to their dashboard
            except Exception as e:
                logger.error(f"Error during registration save or login: {e}")
                messages.error(request, f"Une erreur interne est survenue lors de l\"inscription: {e}")
        else:
            # Form is invalid, errors will be displayed by the template
            messages.error(request, "Erreur d\"inscription. Veuillez vérifier les champs.")
    else:
        form = CitizenRegistrationForm()

    return render(request, "citizens/register.html", {"form": form})

@login_required
def citizen_dashboard(request):
    # Ensure the user is a citizen
    if request.user.user_type != "CITIZEN":
        messages.error(request, "Accès réservé aux citoyens.")
        logout(request) # Log out non-citizens trying to access
        return redirect("login")

    try:
        # Get the related Citizen profile
        citizen = request.user.citizen_profile
    except Citizen.DoesNotExist:
        # This case should ideally not happen if registration is correct
        messages.error(request, "Profil citoyen non trouvé. Veuillez contacter l\"administrateur.")
        logout(request)
        return redirect("login")

    # Fetch data for the dashboard
    recent_problems = Problem.objects.filter(citizen=citizen) \
                                    .select_related("category", "municipality") \
                                    .order_by("-created_at")[:5]
    recent_complaints = Complaint.objects.filter(citizen=citizen) \
                                        .select_related("municipality") \
                                        .order_by("-created_at")[:5]
    problem_count = Problem.objects.filter(citizen=citizen).count()
    complaint_count = Complaint.objects.filter(citizen=citizen).count()
    pending_problems = Problem.objects.filter(citizen=citizen, status="PENDING").count()

    context = {
        "citizen": citizen,
        "recent_problems": recent_problems,
        "recent_complaints": recent_complaints,
        "problem_count": problem_count,
        "complaint_count": complaint_count,
        "pending_problems": pending_problems,
    }
    return render(request, "citizens/dashboard.html", context)

@login_required
def report_problem(request):
    # Ensure the user is a citizen
    if request.user.user_type != "CITIZEN":
        return redirect("login")

    categories = Category.objects.all()
    try:
        citizen = request.user.citizen_profile
    except Citizen.DoesNotExist:
        messages.error(request, "Profil citoyen non trouvé.")
        return redirect("login")

    if request.method == "POST":
        form = ProblemReportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                accuracy = request.POST.get("accuracy")
                # Example check for GPS accuracy, adjust threshold as needed
                if accuracy and float(accuracy) > 1000:
                    messages.error(request, "La précision GPS est trop faible. Essayez de vous rapprocher ou attendez un meilleur signal.")
                    return render(request, "citizens/report_problem.html", {"form": form, "categories": categories})

                problem = form.save(commit=False)
                problem.citizen = citizen

                category_id = request.POST.get("selected_category")
                if category_id:
                    problem.category = get_object_or_404(Category, id=category_id)
                else:
                    messages.error(request, "Veuillez sélectionner une catégorie pour le problème.")
                    return render(request, "citizens/report_problem.html", {"form": form, "categories": categories})

                # Get municipality ID from hidden field populated by JS
                municipality_id = request.POST.get("municipality_id")
                if municipality_id:
                    problem.municipality = get_object_or_404(Municipality, id=municipality_id)
                else:
                    # Handle case where municipality couldn't be determined (e.g., location outside known boundaries)
                    # Depending on requirements, you might assign a default, leave it null, or show an error.
                    # Here, we show a warning and save without municipality.
                    problem.municipality = None
                    messages.warning(request, "Impossible de déterminer la municipalité pour cet emplacement. Le problème sera enregistré sans municipalité associée.")
                    logger.warning(f"Could not determine municipality for problem at ({form.cleaned_data.get("latitude")}, {form.cleaned_data.get("longitude")})")

                problem.save()
                messages.success(request, "Problème signalé avec succès!")
                return redirect("problem_detail", pk=problem.pk)

            except Exception as e:
                logger.error(f"Error reporting problem: {e}")
                messages.error(request, f"Une erreur est survenue lors du signalement du problème: {e}")
        else:
            # Form is invalid
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        # GET request
        form = ProblemReportForm()

    return render(request, "citizens/report_problem.html", {"form": form, "categories": categories})

@login_required
def problem_detail(request, pk):
    if request.user.user_type != "CITIZEN": return redirect("login")

    problem = get_object_or_404(Problem.objects.select_related("citizen__user", "category", "municipality"), pk=pk)
    try:
        citizen = request.user.citizen_profile
    except Citizen.DoesNotExist:
        return redirect("login")

    # Ensure the citizen viewing the detail is the one who reported it
    if problem.citizen != citizen:
        messages.error(request, "Accès non autorisé à ce détail de problème.")
        return redirect("citizen_dashboard")

    context = {
        "problem": problem,
    }
    return render(request, "citizens/problem_detail.html", context)

@login_required
def problem_list(request):
    if request.user.user_type != "CITIZEN": return redirect("login")

    try:
        citizen = request.user.citizen_profile
    except Citizen.DoesNotExist:
        return redirect("login")

    problems = Problem.objects.filter(citizen=citizen).select_related("category", "municipality").order_by("-created_at")

    context = {
        "problems": problems,
    }
    return render(request, "citizens/problem_list.html", context)

@login_required
def submit_complaint(request):
    if request.user.user_type != "CITIZEN":
        return redirect("login")

    try:
        citizen = request.user.citizen_profile
    except Citizen.DoesNotExist:
        return redirect("login")

    if request.method == "POST":
        form = ComplaintForm(request.POST, request.FILES) # Added request.FILES
        if form.is_valid():
            try:
                complaint = form.save(commit=False)
                complaint.citizen = citizen
                complaint.save()
                messages.success(request, "Réclamation soumise avec succès!")
                return redirect("complaint_detail", pk=complaint.id)
            except Exception as e:
                logger.error(f"Error submitting complaint: {e}")
                messages.error(request, f"Une erreur est survenue lors de la soumission: {e}")
        else:
            messages.error(request, "Erreur de soumission. Veuillez vérifier les champs.")
    else:
        form = ComplaintForm()

    context = {
        "form": form,
    }
    return render(request, "citizens/submit_complaint.html", context)

@login_required
def complaint_detail(request, pk):
    if request.user.user_type != "CITIZEN": return redirect("login")

    complaint = get_object_or_404(Complaint.objects.select_related("citizen__user", "municipality"), pk=pk)
    try:
        citizen = request.user.citizen_profile
    except Citizen.DoesNotExist:
        return redirect("login")

    if complaint.citizen != citizen:
        messages.error(request, "Accès non autorisé à ce détail de réclamation.")
        return redirect("citizen_dashboard")

    context = {
        "complaint": complaint,
    }
    return render(request, "citizens/complaint_detail.html", context)

@login_required
def complaint_list(request):
    if request.user.user_type != "CITIZEN": return redirect("login")

    try:
        citizen = request.user.citizen_profile
    except Citizen.DoesNotExist:
        return redirect("login")

    complaints = Complaint.objects.filter(citizen=citizen).select_related("municipality").order_by("-created_at")

    context = {
        "complaints": complaints,
    }
    return render(request, "citizens/complaint_list.html", context)

@login_required
def edit_profile(request):
    if request.user.user_type != "CITIZEN": return redirect("login")

    try:
        citizen = request.user.citizen_profile
    except Citizen.DoesNotExist:
        return redirect("login")

    if request.method == "POST":
        # We only allow editing fields in CitizenProfileForm (full_name, address)
        form = CitizenProfileForm(request.POST, instance=citizen)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Profil mis à jour avec succès!")
                return redirect("citizen_dashboard")
            except Exception as e:
                logger.error(f"Error editing profile: {e}")
                messages.error(request, f"Une erreur est survenue lors de la mise à jour: {e}")
        else:
            messages.error(request, "Erreur de mise à jour. Veuillez vérifier les champs.")
    else:
        form = CitizenProfileForm(instance=citizen)

    context = {
        "form": form,
        # Pass phone number separately for display if needed
        "phone_number": request.user.phone_number,
        "nni": citizen.nni, # Pass NNI for display
        "municipality_name": citizen.municipality.name, # Pass municipality name
    }
    return render(request, "citizens/edit_profile.html", context)


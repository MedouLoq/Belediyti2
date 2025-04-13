# citizens/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate # Import authenticate
from django.db.models import Q # Import Q for complex lookups
from .models import User, Citizen, Problem, Complaint, Municipality, Category
# Import your forms including LoginForm
from .forms import (
    CitizenRegistrationForm, ProblemReportForm, ComplaintForm,
    CitizenProfileForm, LoginForm
)

import json # Import the json library

# Import Shapely AFTER checking for installation
try:
    from shapely.geometry import Point, shape
    SHAPELY_INSTALLED = True
except ImportError:
    SHAPELY_INSTALLED = False
    Point, shape = None, None # Define as None if not installed
# --- Authentication Views ---

def user_login(request):
    if request.user.is_authenticated:
        # Redirect already logged-in users to dashboard
        return redirect('citizen_dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Try authenticating with username first, then email
            user = authenticate(request, username=username_or_email, password=password)
            if user is None:
                 # Check if the input might be an email
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None # Explicitly set to None if email lookup fails

            if user is not None:
                if user.user_type == 'CITIZEN': # Ensure only citizens use this login
                    login(request, user)
                    messages.success(request, f'Connexion réussie! Bonjour {user.username}.')
                    # Redirect to dashboard or intended page
                    next_url = request.GET.get('next')
                    return redirect(next_url or 'citizen_dashboard')
                else:
                    messages.error(request, 'Accès non autorisé pour ce type d\'utilisateur.')
            else:
                messages.error(request, 'Nom d\'utilisateur/Email ou mot de passe incorrect.')
        else:
            # If form is invalid (e.g., fields missing), errors are in form.errors
            # You could add a generic message or rely on template display
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')

    else: # GET request
        form = LoginForm()

    return render(request, 'citizens/login.html', {'form': form})

@login_required # Ensure user is logged in to log out
def user_logout(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login') # Redirect to login page after logout

def register(request):
    if request.user.is_authenticated:
        return redirect('citizen_dashboard')

    if request.method == 'POST':
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save() # The overridden save method handles Citizen creation

            login(request, user)
            messages.success(request, 'Votre compte a été créé et vous êtes connecté!')
            return redirect('citizen_dashboard')
        else:
             messages.error(request, 'Erreur lors de l\'inscription. Veuillez vérifier les informations.')
    else:
        form = CitizenRegistrationForm()

    return render(request, 'citizens/register.html', {'form': form})


# --- Citizen Dashboard and Core Features ---

@login_required
def citizen_dashboard(request):
    if request.user.user_type != 'CITIZEN':
        messages.error(request, "Accès réservé aux citoyens.")
        logout(request)
        return redirect('login')

    try:
        citizen = Citizen.objects.select_related('user').get(user=request.user)
    except Citizen.DoesNotExist:
        messages.error(request, "Profil citoyen non trouvé. Veuillez contacter l'administrateur.")
        logout(request)
        return redirect('login')

    # Retrieve recent entries (limit to 5)
    recent_problems = Problem.objects.filter(citizen=citizen) \
                                     .select_related('category', 'municipality') \
                                     .order_by('-created_at')[:5]
    recent_complaints = Complaint.objects.filter(citizen=citizen) \
                                         .select_related('municipality') \
                                         .order_by('-created_at')[:5]
    problem_count = Problem.objects.filter(citizen=citizen).count()
    complaint_count = Complaint.objects.filter(citizen=citizen).count()
    pending_problems = Problem.objects.filter(citizen=citizen, status='PENDING').count()

    context = {
        'citizen': citizen,
        'recent_problems': recent_problems,
        'recent_complaints': recent_complaints,
        'problem_count': problem_count,
        'complaint_count': complaint_count,
        'pending_problems': pending_problems,
    }
    return render(request, 'citizens/dashboard.html', context)

# --- Problem Views ---

# citizens/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Problem, Category, Municipality, Citizen # Ensure all are imported
from .forms import ProblemReportForm
import json # Import the json library

# Import Shapely conditionally AFTER checking for installation
try:
    from shapely.geometry import Point, shape
    SHAPELY_INSTALLED = True
    print("DEBUG: Shapely library successfully imported.")
except ImportError:
    SHAPELY_INSTALLED = False
    Point, shape = None, None # Define as None if not installed
    print("DEBUG WARNING: Shapely library not found. Municipality check will be limited.")

# =========================================================================
# Your other views (login, register, dashboard, etc.)
# =========================================================================
@login_required
def report_problem(request):
    categories = Category.objects.all()
    if request.method == "POST":
        form = ProblemReportForm(request.POST, request.FILES)
        if form.is_valid():
            citizen = get_object_or_404(Citizen, user=request.user)
            problem = form.save(commit=False)
            problem.citizen = citizen

            # Get the selected category from the hidden input.
            category_id = request.POST.get("selected_category")
            if category_id:
                problem.category = get_object_or_404(Category, id=category_id)
            else:
                messages.error(request, "Veuillez sélectionner une catégorie.")
                return render(request, "citizens/report_problem.html", {"form": form, "categories": categories})

            # Retrieve the municipality candidate from the hidden input.
            municipality_candidate = request.POST.get("municipality_candidate", "").strip()
            if municipality_candidate:
                # Use a more flexible lookup.
                municipality = Municipality.objects.filter(name__icontains=municipality_candidate).first()
                if not municipality:
                    # Optionally, if no record found, you might log this or fallback.
                    municipality = Municipality.objects.first()
            else:
                municipality = Municipality.objects.first()

            if not municipality:
                messages.error(request, "Aucune municipalité configurée dans le système.")
                return render(request, "citizens/report_problem.html", {"form": form, "categories": categories})

            problem.municipality = municipality
            problem.save()
            messages.success(request, "Votre problème a été signalé avec succès!")
            return redirect("problem_detail", pk=problem.pk)
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ProblemReportForm()

    return render(request, "citizens/report_problem.html", {"form": form, "categories": categories})


# =========================================================================
# Other views...
# =========================================================================
#
@login_required
def problem_detail(request, pk):
    if request.user.user_type != 'CITIZEN': return redirect('login')

    # Use select_related for efficiency
    problem = get_object_or_404(Problem.objects.select_related('citizen__user', 'category', 'municipality'), pk=pk)
    citizen = get_object_or_404(Citizen, user=request.user)

    # *** Security Check: Ensure the logged-in citizen owns this problem ***
    if problem.citizen != citizen:
        messages.error(request, "Vous n'êtes pas autorisé à voir ce problème.")
        return redirect('citizen_dashboard')

    # Fetch status logs for this problem (optional)
    # status_logs = StatusLog.objects.filter(record_type='PROBLEM', record_id=problem.id).order_by('-changed_at').select_related('changed_by')

    context = {
        'problem': problem,
        # 'status_logs': status_logs
    }

    return render(request, 'citizens/problem_detail.html', context)

@login_required
def problem_list(request):
    if request.user.user_type != 'CITIZEN': return redirect('login')

    citizen = get_object_or_404(Citizen, user=request.user)
    # Use select_related for efficiency, fetch all problems for the citizen
    problems = Problem.objects.filter(citizen=citizen).select_related('category', 'municipality').order_by('-created_at')

    context = {
        'problems': problems,
    }

    return render(request, 'citizens/problem_list.html', context)

# --- Complaint Views ---

@login_required
def submit_complaint(request):
    if request.user.user_type != 'CITIZEN':
        return redirect('login')

    citizen = get_object_or_404(Citizen, user=request.user)

    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.citizen = citizen 
            
            # Now complaint.municipality will have the value selected by the user.
            complaint.save()

            messages.success(request, 'Votre réclamation a été soumise avec succès!')
            return redirect('complaint_detail', pk=complaint.id)
        else:
            messages.error(request, 'Erreur lors de la soumission. Veuillez vérifier les informations.')
    else:
        form = ComplaintForm()

    context = {
        'form': form,
    }
    return render(request, 'citizens/submit_complaint.html', context)



@login_required
def complaint_detail(request, pk):
    if request.user.user_type != 'CITIZEN': return redirect('login')

    complaint = get_object_or_404(Complaint.objects.select_related('citizen__user', 'municipality'), pk=pk)
    citizen = get_object_or_404(Citizen, user=request.user)

    # *** Security Check ***
    if complaint.citizen != citizen:
        messages.error(request, "Vous n'êtes pas autorisé à voir cette réclamation.")
        return redirect('citizen_dashboard')

    # Fetch status logs (optional)
    # status_logs = StatusLog.objects.filter(record_type='COMPLAINT', record_id=complaint.id).order_by('-changed_at').select_related('changed_by')

    context = {
        'complaint': complaint,
        # 'status_logs': status_logs
    }

    return render(request, 'citizens/complaint_detail.html', context)

@login_required
def complaint_list(request):
    if request.user.user_type != 'CITIZEN': return redirect('login')

    citizen = get_object_or_404(Citizen, user=request.user)
    complaints = Complaint.objects.filter(citizen=citizen).select_related('municipality').order_by('-created_at')

    context = {
        'complaints': complaints,
    }

    return render(request, 'citizens/complaint_list.html', context)


# --- Profile View ---

@login_required
def edit_profile(request):
    if request.user.user_type != 'CITIZEN': return redirect('login')

    citizen = get_object_or_404(Citizen, user=request.user)
    user = request.user # Get the user object too if you need to edit User fields (like email)

    if request.method == 'POST':
        # You might want separate forms if editing User and Citizen data
        form = CitizenProfileForm(request.POST, instance=citizen)
        # user_form = UserChangeForm(request.POST, instance=user) # Example if editing user

        if form.is_valid(): # Add 'and user_form.is_valid()' if using user form
            form.save()
            # user_form.save() # If editing user details
            messages.success(request, 'Votre profil a été mis à jour avec succès!')
            return redirect('citizen_dashboard') # Or redirect back to edit profile page
        else:
            messages.error(request, 'Erreur lors de la mise à jour du profil.')
    else: # GET Request
        form = CitizenProfileForm(instance=citizen)
        # user_form = UserChangeForm(instance=user)

    context = {
        'form': form,
        # 'user_form': user_form
    }

    return render(request, 'citizens/edit_profile.html', context)
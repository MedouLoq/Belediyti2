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
    name = request.GET.get('name', '').strip()
    lat = float(request.GET.get('lat', 0))
    lon = float(request.GET.get('lon', 0))
    
    logger.debug(f"Received municipality name: '{name}', lat: {lat}, lon: {lon}")
    
    if not name:
        logger.warning("No municipality name provided")
        return JsonResponse({'municipality_id': ''})
    
    # Log all municipalities in the database for debugging
    all_municipalities = list(Municipality.objects.all().values_list('name', flat=True))
    logger.debug(f"All municipalities in database: {all_municipalities}")
    
    # Try exact match (case-insensitive, after stripping whitespace)
    municipality = Municipality.objects.filter(name__iexact=name.strip()).first()
    if municipality:
        logger.debug(f"Exact match found: {municipality.name} (ID: {municipality.id})")
        return JsonResponse({'municipality_id': municipality.id})
    
    # Try partial match
    municipality = Municipality.objects.filter(name__icontains=name.strip()).first()
    if municipality:
        logger.debug(f"Partial match found: {municipality.name} (ID: {municipality.id})")
        return JsonResponse({'municipality_id': municipality.id})
    
    # Specific handling for Ksar
    if name.lower().strip() == 'ksar':
        municipality = Municipality.objects.filter(name__iexact='Ksar').first()
        if municipality:
            logger.debug(f"Ksar match found: {municipality.name} (ID: {municipality.id})")
            return JsonResponse({'municipality_id': municipality.id})
    
    # Boundary check if shapely is available
    if SHAPELY_INSTALLED and lat and lon:
        point = Point(lon, lat)
        for mun in Municipality.objects.exclude(boundary__isnull=True).exclude(boundary=''):
            try:
                boundary = json.loads(mun.boundary)
                if boundary and shape(boundary).contains(point):
                    logger.debug(f"Boundary match found: {mun.name} (ID: {mun.id})")
                    return JsonResponse({'municipality_id': mun.id})
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Boundary error for {mun.name}: {e}")
                continue
    
    logger.warning(f"No municipality found for name: '{name}'")
    return JsonResponse({'municipality_id': ''})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('citizen_dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username_or_email, password=password)
            if user is None:
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None

            if user is not None:
                if user.user_type == 'CITIZEN':
                    login(request, user)
                    messages.success(request, f'Connexion réussie! Bonjour {user.username}.')
                    next_url = request.GET.get('next')
                    return redirect(next_url or 'citizen_dashboard')
                else:
                    messages.error(request, 'Accès non autorisé.')
            else:
                messages.error(request, 'Identifiants incorrects.')
        else:
            messages.error(request, 'Veuillez corriger les erreurs.')
    else:
        form = LoginForm()

    return render(request, 'citizens/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('login')

def register(request):
    if request.user.is_authenticated:
        return redirect('citizen_dashboard')

    if request.method == 'POST':
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Compte créé et connecté!')
            return redirect('citizen_dashboard')
        else:
            messages.error(request, 'Erreur d\'inscription.')
    else:
        form = CitizenRegistrationForm()

    return render(request, 'citizens/register.html', {'form': form})

@login_required
def citizen_dashboard(request):
    if request.user.user_type != 'CITIZEN':
        messages.error(request, "Accès réservé aux citoyens.")
        logout(request)
        return redirect('login')

    try:
        citizen = Citizen.objects.select_related('user').get(user=request.user)
    except Citizen.DoesNotExist:
        messages.error(request, "Profil citoyen non trouvé.")
        logout(request)
        return redirect('login')

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

@login_required
def report_problem(request):
    categories = Category.objects.all()
    if request.method == "POST":
        form = ProblemReportForm(request.POST, request.FILES)
        if form.is_valid():
            accuracy = request.POST.get("accuracy")
            if accuracy and float(accuracy) > 1000:
                messages.error(request, "Précision GPS trop faible.")
                return render(request, "citizens/report_problem.html", {"form": form, "categories": categories})
            
            citizen = get_object_or_404(Citizen, user=request.user)
            problem = form.save(commit=False)
            problem.citizen = citizen
            
            category_id = request.POST.get("selected_category")
            if category_id:
                problem.category = get_object_or_404(Category, id=category_id)
            else:
                messages.error(request, "Sélectionnez une catégorie.")
                return render(request, "citizens/report_problem.html", {"form": form, "categories": categories})
            
            # Try to get municipality_id first
            municipality_id = request.POST.get("municipality_id")
            if municipality_id:
                problem.municipality = get_object_or_404(Municipality, id=municipality_id)
            else:
                # Fallback to municipality_candidate
                municipality_candidate = request.POST.get("municipality_candidate", '').strip()
                if municipality_candidate:
                    municipality = Municipality.objects.filter(name__iexact=municipality_candidate).first()
                    if municipality:
                        problem.municipality = municipality
                    else:
                        logger.warning(f"Municipality '{municipality_candidate}' not found in database during form submission")
                        # Allow submission without municipality
                        problem.municipality = None
                        messages.warning(request, "Municipalité non trouvée dans la base. Le problème sera enregistré sans municipalité.")
                else:
                    # No municipality identified
                    problem.municipality = None
                    messages.warning(request, "Aucune municipalité identifiée. Le problème sera enregistré sans municipalité.")
            
            problem.save()
            messages.success(request, "Problème signalé!")
            return redirect("problem_detail", pk=problem.pk)
        else:
            messages.error(request, "Corrigez les erreurs.")
    else:
        form = ProblemReportForm()

    return render(request, "citizens/report_problem.html", {"form": form, "categories": categories})

@login_required
def problem_detail(request, pk):
    if request.user.user_type != 'CITIZEN': return redirect('login')

    problem = get_object_or_404(Problem.objects.select_related('citizen__user', 'category', 'municipality'), pk=pk)
    citizen = get_object_or_404(Citizen, user=request.user)

    if problem.citizen != citizen:
        messages.error(request, "Accès non autorisé.")
        return redirect('citizen_dashboard')

    context = {
        'problem': problem,
    }
    return render(request, 'citizens/problem_detail.html', context)

@login_required
def problem_list(request):
    if request.user.user_type != 'CITIZEN': return redirect('login')

    citizen = get_object_or_404(Citizen, user=request.user)
    problems = Problem.objects.filter(citizen=citizen).select_related('category', 'municipality').order_by('-created_at')

    context = {
        'problems': problems,
    }
    return render(request, 'citizens/problem_list.html', context)

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
            complaint.save()
            messages.success(request, 'Réclamation soumise!')
            return redirect('complaint_detail', pk=complaint.id)
        else:
            messages.error(request, 'Erreur de soumission.')
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

    if complaint.citizen != citizen:
        messages.error(request, "Accès non autorisé.")
        return redirect('citizen_dashboard')

    context = {
        'complaint': complaint,
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

@login_required
def edit_profile(request):
    if request.user.user_type != 'CITIZEN': return redirect('login')

    citizen = get_object_or_404(Citizen, user=request.user)

    if request.method == 'POST':
        form = CitizenProfileForm(request.POST, instance=citizen)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour!')
            return redirect('citizen_dashboard')
        else:
            messages.error(request, 'Erreur de mise à jour.')
    else:
        form = CitizenProfileForm(instance=citizen)

    context = {
        'form': form,
    }
    return render(request, 'citizens/edit_profile.html', context)
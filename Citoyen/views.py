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

from difflib import SequenceMatcher


logger = logging.getLogger(__name__)

try:
    from shapely.geometry import Point, shape
    SHAPELY_INSTALLED = True
except ImportError:
    SHAPELY_INSTALLED = False
    Point, shape = None, None

def similarity_ratio(a, b):
    """Calculate similarity ratio between two strings (0-1, where 1 is exact match)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def get_municipality_id(request):
    name_param = request.GET.get("name", "").strip()
    lat_param = request.GET.get("lat")
    lon_param = request.GET.get("lon")

    lat = float(lat_param) if lat_param else None
    lon = float(lon_param) if lon_param else None

    logger.debug(f"Received municipality lookup: name=\"{name_param}\", lat={lat}, lon={lon}")

    if not name_param:
        logger.warning("No municipality name provided for lookup.")
        return JsonResponse({"municipality_id": ""})

    # Normalize the input name (lowercase, stripped)
    normalized_name = name_param.lower()

    # 1. Try exact match (case-insensitive)
    municipality = Municipality.objects.filter(name__iexact=normalized_name).first()
    if municipality:
        logger.debug(f"Exact match found: {municipality.name} (ID: {municipality.id}) for input \"{name_param}\"")
        return JsonResponse({"municipality_id": municipality.id})

    # 2. Try if provided name CONTAINS database name (e.g., "Tevragh Zeina" contains "Tevragh Zein")
    all_municipalities = Municipality.objects.all()
    for mun in all_municipalities:
        db_name_normalized = mun.name.lower().strip()
        if db_name_normalized and normalized_name.startswith(db_name_normalized):
             logger.debug(f"Provided name contains DB name match: DB=\"{mun.name}\" contains in Input=\"{name_param}\" (ID: {mun.id})")
             return JsonResponse({"municipality_id": mun.id})

    # 3. Try if database name CONTAINS provided name (original partial match)
    municipality = Municipality.objects.filter(name__icontains=normalized_name).first()
    if municipality:
        logger.debug(f"DB name contains provided name match: DB=\"{municipality.name}\" contains Input=\"{name_param}\" (ID: {municipality.id})")
        return JsonResponse({"municipality_id": municipality.id})

    # 4. NEW: Fuzzy matching for typos and spelling variations
    best_match = None
    best_similarity = 0.0
    similarity_threshold = 0.8  # Adjust this threshold as needed (0.8 = 80% similarity)
    
    for mun in all_municipalities:
        similarity = similarity_ratio(normalized_name, mun.name)
        if similarity > similarity_threshold and similarity > best_similarity:
            best_similarity = similarity
            best_match = mun
    
    if best_match:
        logger.debug(f"Fuzzy match found: DB=\"{best_match.name}\" matches Input=\"{name_param}\" with {best_similarity:.2%} similarity (ID: {best_match.id})")
        return JsonResponse({"municipality_id": best_match.id})

    # 5. Boundary check if shapely is available and coordinates provided
    if SHAPELY_INSTALLED and lat is not None and lon is not None:
        point = Point(lon, lat)
        # Optimize: Exclude municipalities without boundaries first
        municipalities_with_boundaries = Municipality.objects.exclude(boundary__isnull=True).exclude(boundary="")
        for mun in municipalities_with_boundaries:
            try:
                # Basic validation: Check if boundary is a string and looks like JSON
                if isinstance(mun.boundary, str) and mun.boundary.strip().startswith("{"):
                    boundary_geojson = json.loads(mun.boundary)
                    # Ensure it has a geometry type (basic check)
                    if boundary_geojson and boundary_geojson.get("type") and boundary_geojson.get("coordinates"):
                        boundary_shape = shape(boundary_geojson)
                        if boundary_shape.is_valid and boundary_shape.contains(point):
                            logger.debug(f"Boundary match found: {mun.name} (ID: {mun.id}) for point ({lon}, {lat})")
                            return JsonResponse({"municipality_id": mun.id})
                    else:
                         logger.warning(f"Invalid GeoJSON structure for {mun.name}: Missing type or coordinates")
                else:
                    logger.warning(f"Invalid boundary data type or format for {mun.name}: {type(mun.boundary)}")
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.error(f"Error processing boundary for {mun.name} (ID: {mun.id}): {e}")
            except Exception as e:
                 logger.error(f"Unexpected error processing boundary for {mun.name} (ID: {mun.id}): {e}")

    # Fixed the logging statement to include the actual name_param
    logger.warning(f"No municipality found for name: \"{name_param}\"")
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
            return redirect("Muni_admin:dashboard")
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


# Citoyen/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token
from .forms import LoginForm # Import your LoginForm
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])  # Allow unauthenticated access for login
def login_api(request):
    form = LoginForm(data=request.data)  # Use request.data for DRF
    if form.is_valid():
        identifier = form.cleaned_data.get('identifier')
        password = form.cleaned_data.get('password')
        user = authenticate(request, username=identifier, password=password)
        if user is not None:
            login(request, user) # Django login for session if needed
            token, _ = Token.objects.get_or_create(user=user) # Get or create a token
            return Response({'token': token.key, 'message': 'Login successful'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    else:
         logger.error(f"Login form errors: {form.errors}") # Log the form errors
         return Response({'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST) # Return detailed form errors

@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    form = CitizenRegistrationForm(data=request.data)
    if form.is_valid():
        try:
            user = form.save() # Save the user using the form
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'message': 'Registration successful'}, status=status.HTTP_201_CREATED) # Return token on success
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            return Response({'error': 'Registration failed', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        logger.error(f"Registration form errors: {form.errors}")
        return Response({'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST) # Return detailed form errors
    
@api_view(['GET'])
@permission_classes([AllowAny])
def municipality_list_api(request):
    municipalities = Municipality.objects.all().values('id', 'name') # Get id and name
    return Response(list(municipalities)) # Serialize to list for JSON


# Citoyen/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import UserSerializer  # Create a serializer for User model
from rest_framework.parsers import MultiPartParser, FormParser # Needed for file uploads

from .models import User, Citizen # Import necessary models
from .serializers import UserSerializer, CitizenProfileUpdateSerializer # Import the serializers we created
from rest_framework.decorators import api_view, permission_classes, parser_classes
# --- Updated User Profile API (GET) ---
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile_api(request):
    """API endpoint to get the authenticated user's profile (including citizen details)."""
    # Pass context to the serializer to build absolute URLs for images
    serializer = UserSerializer(request.user, context={"request": request})
    return Response(serializer.data)

# --- New/Updated Citizen Profile Update API (GET, PUT, PATCH) ---
@api_view(["GET", "PUT", "PATCH"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser]) # Add parsers for file upload
def citizen_profile_update_api(request):
    """API endpoint for retrieving and updating the authenticated citizen's profile."""
    try:
        # Get the Citizen profile related to the authenticated user
        citizen_profile = request.user.citizen_profile
    except Citizen.DoesNotExist:
        return Response({"error": "Citizen profile not found."}, status=status.HTTP_404_NOT_FOUND)
    except AttributeError:
         # Handle cases where the user might not be a citizen (e.g., admin logged in)
        return Response({"error": "User does not have a citizen profile."}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "GET":
        # Use the update serializer for GET as well, so frontend knows which fields are editable
        # Or you could use the nested UserSerializer if you prefer showing all user+profile data
        serializer = CitizenProfileUpdateSerializer(citizen_profile, context={"request": request})
        return Response(serializer.data)

    elif request.method == "PUT" or request.method == "PATCH":
        # Use partial=True for PATCH to allow partial updates
        partial_update = request.method == "PATCH"
        serializer = CitizenProfileUpdateSerializer(
            citizen_profile, 
            data=request.data, 
            partial=partial_update, 
            context={"request": request}
        )
        
        if serializer.is_valid():
            serializer.save()
            # Return the updated profile data, including the new image URL if updated
            # Re-serialize with the UserSerializer to get the full nested structure if needed by Flutter
            # Or just return the CitizenProfileUpdateSerializer data
            updated_user_serializer = UserSerializer(request.user, context={"request": request})
            return Response(updated_user_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Citoyen/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Problem, Complaint, Citizen  # Import your models

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats_api(request):
    try:
        citizen = request.user.citizen_profile # Get citizen from user
    except Citizen.DoesNotExist:
        return Response({'error': 'Citizen profile not found'}, status=404)

    problem_count = Problem.objects.filter(citizen=citizen).count()
    pending_problems = Problem.objects.filter(citizen=citizen, status="PENDING").count()
    complaint_count = Complaint.objects.filter(citizen=citizen).count()
    resolved_problems = Problem.objects.filter(citizen=citizen, status="RESOLVED").count() # Add resolved problems

    data = {
        'problem_count': problem_count,
        'pending_problems': pending_problems,
        'complaint_count': complaint_count,
        'resolved_problems': resolved_problems,
    }
    return Response(data)

# Citoyen/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import StatusLog
from .serializers import StatusLogSerializer  # Create a serializer for StatusLog
from django.db.models import Q

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Problem, Complaint
from .serializers import ProblemSerializer, ComplaintSerializer  # Create serializers
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # Implemented Pagination
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_activity_api(request):
    try:
        citizen = request.user.citizen_profile
    except Citizen.DoesNotExist:
        logger.warning("Citizen profile not found")
        return Response({'error': 'Citizen profile not found'}, status=404)

    try:
        recent_problems = list(Problem.objects.filter(citizen=citizen))
        recent_complaints = list(Complaint.objects.filter(citizen=citizen))
        
        combined_activities = recent_problems + recent_complaints
        
        # Sort combined activities by created_at descending
        combined_activities.sort(key=lambda x: x.created_at, reverse=True)
        
        # Paginate manually
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
        
        paginator = Paginator(combined_activities, 5)  # 5 per page
        page_number = request.GET.get('page', 1)
        
        try:
            activities = paginator.page(page_number)
        except PageNotAnInteger:
            activities = paginator.page(1)
        except EmptyPage:
            return Response([])
        
        # Find this section in recent_activity_api function
        serialized_activities = []
        for activity in activities:
            activity_data = None
            if isinstance(activity, Problem):
                activity_data = ProblemSerializer(activity).data
                activity_data['record_type'] = 'PROBLEM'
                activity_data['title'] = f"Problème: {activity.description[:30]}..." if len(activity.description) > 30 else f"Problème: {activity.description}"
            elif isinstance(activity, Complaint):
                activity_data = ComplaintSerializer(activity).data
                activity_data['record_type'] = 'COMPLAINT'
                activity_data['title'] = f"Réclamation: {activity.subject}"
            
            if activity_data:
                activity_data['changed_at'] = activity.created_at.isoformat()
                serialized_activities.append(activity_data)
            
        
        return Response(serialized_activities)
        
    except Exception as e:
        logger.error(f"Error fetching recent activity: {e}", exc_info=True)
        return Response({'error': f'Error fetching recent activity: {e}'}, status=500)

# In belediyti_project/Belediyti2/Citoyen/views.py, add these API views:

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def problem_list_api(request):
    try:
        citizen = request.user.citizen_profile
        problems = Problem.objects.filter(citizen=citizen).order_by('-created_at')
        
        # Serialize problems with related data
        serialized_problems = []
        for problem in problems:
            problem_data = {
                'id': str(problem.id),
                'description': problem.description,
                'latitude': problem.latitude,
                'longitude': problem.longitude,
                'status': problem.status,
                'created_at': problem.created_at.isoformat(),
                'updated_at': problem.updated_at.isoformat() if problem.updated_at else None,
                'image': request.build_absolute_uri(problem.photo.url) if problem.photo else None,
            }
            
            # Add category if available
            if problem.category:
                problem_data['category'] = {
                    'id': str(problem.category.id),
                    'name': problem.category.name,
                }
            
            # Add municipality if available
            if problem.municipality:
                problem_data['municipality'] = {
                    'id': str(problem.municipality.id),
                    'name': problem.municipality.name,
                }
            
            serialized_problems.append(problem_data)
        
        return Response(serialized_problems)
    except Exception as e:
        logger.error(f"Error fetching problems: {e}", exc_info=True)
        return Response({'error': str(e)}, status=500)

from .serializers import ProblemDetailSerializer # 
import logging

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated]) # Ensure user is logged in
def problem_detail_api(request, pk):
    """
    API endpoint to retrieve details of a specific problem.
    Requires authentication. Ensures the user is the citizen who reported it.
    """
    try:
        # Get the citizen profile associated with the logged-in user
        # Use try-except in case the user is not a citizen or profile doesn't exist
        try:
            requesting_citizen = request.user.citizen_profile
        except Citizen.DoesNotExist:
             logger.warning(f"User {request.user.id} ({request.user.username}) does not have a citizen profile.")
             return Response({"detail": "Profil citoyen non trouvé pour cet utilisateur."}, status=status.HTTP_403_FORBIDDEN)
        except AttributeError:
             logger.warning(f"User {request.user.id} ({request.user.username}) is not a citizen type or lacks citizen_profile attribute.")
             return Response({"detail": "Accès réservé aux citoyens."}, status=status.HTTP_403_FORBIDDEN)

        # Fetch the problem, ensuring it belongs to the requesting citizen
        problem = get_object_or_404(
            Problem.objects.select_related("category", "municipality", "citizen__user"), # Select related fields for efficiency
            pk=pk,
            citizen=requesting_citizen # Security check: only owner can view
        )

    except Problem.DoesNotExist:
        logger.warning(f"Problem with pk={pk} not found for citizen {requesting_citizen.id}")
        return Response({"detail": "Problème non trouvé ou accès non autorisé."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching problem detail for pk={pk}, user {request.user.id}: {e}", exc_info=True)
        return Response({"detail": "Une erreur interne est survenue."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Pass request context to serializer to build absolute URLs
    serializer = ProblemDetailSerializer(problem, context={"request": request})
    return Response(serializer.data)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
# Import your models: Problem, Citizen, Category, Municipality
import logging

logger = logging.getLogger(__name__)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_problem_api(request):
    try:
        citizen = request.user.citizen_profile

        # Validate required fields (description, lat, lon, category)
        required_fields = ["description", "latitude", "longitude", "category"]
        for field in required_fields:
            if field not in request.data:
                return Response({"error": f"Missing required field: {field}"}, status=400)

        # Create new problem instance
        problem = Problem(
            citizen=citizen,
            description=request.data["description"],
            latitude=float(request.data["latitude"]),
            longitude=float(request.data["longitude"]),
            # Add other non-file fields from request.data if applicable
        )

        # Set category
        try:
            category_id = request.data["category"]
            problem.category = get_object_or_404(Category, id=category_id)
        except Exception as e:
            return Response({"error": f"Invalid category: {e}"}, status=400)

        # Set municipality (handle potential absence)
        if "municipality" in request.data and request.data["municipality"]:
            try:
                municipality_id = request.data["municipality"]
                problem.municipality = get_object_or_404(Municipality, id=municipality_id)
            except Exception as e:
                logger.warning(f"Could not set municipality: {e}")
                problem.municipality = None # Explicitly set to None if optional

        # Handle individual file uploads
        if "photo" in request.FILES:
            problem.photo = request.FILES["photo"]
        if "video" in request.FILES:
            # Add validation for video file types/size if needed
            problem.video = request.FILES["video"]
        if "voice_record" in request.FILES:
            # Add validation for audio file types/size if needed
            problem.voice_record = request.FILES["voice_record"]
        if "document" in request.FILES:
            # Add validation for document file types/size if needed
            problem.document = request.FILES["document"]

        # Save the problem object with all fields assigned
        problem.save()

        # Prepare response
        # Consider serializing the problem object for a more complete response
        return Response({
            "id": str(problem.id),
            "description": problem.description,
            "status": problem.status,
            "created_at": problem.created_at.isoformat(),
            "message": "Problem reported successfully."
            # Optionally include URLs to uploaded files if needed by the client
            # "photo_url": problem.photo.url if problem.photo else None,
            # "video_url": problem.video.url if problem.video else None,
            # ... etc.
        }, status=201)

    except Exception as e:
        logger.error(f"Error reporting problem: {e}", exc_info=True)
        return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_list_api(request):
    try:
        categories = Category.objects.all()
        
        serialized_categories = []
        for category in categories:
            serialized_categories.append({
                'id': str(category.id),
                'name': category.name,
            })
        
        return Response(serialized_categories)
    except Exception as e:
        logger.error(f"Error fetching categories: {e}", exc_info=True)
        return Response({'error': str(e)}, status=500)
    
# In belediyti_project/Belediyti2/Citoyen/views.py, add these API views:
from .models import Notification
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list_api(request):
    try:
        # Assuming you have a Notification model with a user field
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        
        serialized_notifications = []
        for notification in notifications:
            notification_data = {
                'id': str(notification.id),
                'title': notification.title,
                'message': notification.message,
                'type': notification.type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'reference_id': str(notification.related_id) if notification.related_id else None,
            }
            serialized_notifications.append(notification_data)
        
        return Response(serialized_notifications)
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}", exc_info=True)
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read_api(request, pk):
    try:
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({'success': True})
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}", exc_info=True)
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read_api(request):
    try:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'success': True})
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}", exc_info=True)
        return Response({'error': str(e)}, status=500)


import random
import requests
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import VerificationCode
from django.utils import timezone
from django.conf import settings

User = get_user_model()

# Chinguisoft API Configuration
CHINGUISOFT_VALIDATION_KEY = settings.CHINGUISOFT_VALIDATION_KEY # Replace with your actual key
CHINGUISOFT_VALIDATION_TOKEN =  settings.CHINGUISOFT_VALIDATION_TOKEN # Replace with your actual token
CHINGUISOFT_API_URL = f'https://chinguisoft.com/api/sms/validation/{CHINGUISOFT_VALIDATION_KEY}'

def generate_code():
    """Generate a 6-digit verification code"""
    return f"{random.randint(100000, 999999)}"

def send_sms_verification_chinguisoft(phone_number, language='ar', custom_code=None):
    """
    Send SMS verification using Chinguisoft API
    
    Args:
        phone_number (str): Phone number (8 digits starting with 2, 3, or 4)
        language (str): Language preference ('ar' for Arabic, 'fr' for French)
        custom_code (str, optional): Custom verification code (3-6 digits)
    
    Returns:
        dict: Response containing success status, code, and balance
    """
    try:
        headers = {
            'Validation-token': CHINGUISOFT_VALIDATION_TOKEN,
            'Content-Type': 'application/json',
        }
        
        payload = {
            'phone': phone_number,
            'lang': language,
        }
        
        # Add custom code if provided
        if custom_code:
            payload['code'] = custom_code
        
        print(f"Sending SMS to {phone_number} in {language} language...")
        
        response = requests.post(
            CHINGUISOFT_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"SMS sent successfully. Code: {response_data.get('code')}, Balance: {response_data.get('balance')}")
            return {
                'success': True,
                'code': response_data.get('code'),
                'balance': response_data.get('balance'),
                'message': 'SMS sent successfully'
            }
        elif response.status_code == 422:
            # Validation errors
            error_data = response.json()
            print(f"Validation errors: {error_data}")
            return {
                'success': False,
                'error': 'Validation failed',
                'details': error_data.get('errors', {})
            }
        elif response.status_code == 429:
            # Too many requests
            print("Too many requests - rate limited")
            return {
                'success': False,
                'error': 'Too many requests, please slow down'
            }
        elif response.status_code == 401:
            # Unauthorized
            print("Unauthorized - invalid validation key or token")
            return {
                'success': False,
                'error': 'Unauthorized access'
            }
        elif response.status_code == 402:
            # Payment required
            payment_data = response.json()
            print(f"Insufficient balance: {payment_data}")
            return {
                'success': False,
                'error': 'Insufficient balance',
                'balance': payment_data.get('balance', 0)
            }
        elif response.status_code == 503:
            # Service unavailable
            print("Service temporarily unavailable")
            return {
                'success': False,
                'error': 'Service temporarily unavailable'
            }
        else:
            print(f"Unexpected error: {response.status_code} - {response.text}")
            return {
                'success': False,
                'error': f'Unexpected error: {response.status_code}'
            }
            
    except requests.exceptions.Timeout:
        print("Request timeout")
        return {
            'success': False,
            'error': 'Request timeout'
        }
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")
        return {
            'success': False,
            'error': 'Network error'
        }
    except Exception as e:
        print(f"Unexpected exception: {e}")
        return {
            'success': False,
            'error': 'Unknown error occurred'
        }

def store_verification_code(phone_number, code):
    """Store verification code in database"""
    try:
        # Get user by phone number
        user = User.objects.get(phone_number=phone_number)
        
        # Delete any existing verification codes for this user
        VerificationCode.objects.filter(user=user).delete()
        
        # Create new verification code
        VerificationCode.objects.create(
            user=user,
            code=code
        )
        return True
    except User.DoesNotExist:
        print(f"User with phone number {phone_number} not found")
        return False
    except Exception as e:
        print(f"Error storing verification code: {e}")
        return False

def verify_stored_code(phone_number, code):
    """Verify code against stored code in database"""
    try:
        # Get user by phone number
        user = User.objects.get(phone_number=phone_number)
        
        # Get the most recent verification code
        verification_code = VerificationCode.objects.filter(user=user).order_by('-created_at').first()
        
        if not verification_code:
            print("No verification code found for user")
            return False
        
        if verification_code.is_expired():
            print("Verification code has expired")
            # Clean up expired code
            verification_code.delete()
            return False
        
        if verification_code.code == code:
            # Code is correct, clean up and return success
            verification_code.delete()
            return True
        else:
            print("Invalid verification code")
            return False
            
    except User.DoesNotExist:
        print(f"User with phone number {phone_number} not found")
        return False
    except Exception as e:
        print(f"Error verifying code: {e}")
        return False

class SendVerificationCodeView(APIView):
    def post(self, request):
        phone_number_local = request.data.get("phone_number")
        language = request.data.get("language", "ar")  # Default to Arabic
        
        # Validate phone number format (8 digits starting with 2, 3, or 4)
        if not phone_number_local:
            return Response({"error": "Phone number is required."}, status=400)
        
        # Remove any spaces or special characters
        phone_number_clean = ''.join(filter(str.isdigit, phone_number_local))
        
        # Validate format according to Chinguisoft requirements
        if len(phone_number_clean) != 8 or not phone_number_clean[0] in ['2', '3', '4']:
            return Response({
                "error": "Invalid phone number format. Must be 8 digits starting with 2, 3, or 4."
            }, status=400)
        
        # Validate language
        if language not in ['ar', 'fr']:
            language = 'ar'  # Default to Arabic if invalid
        
        try:
            print(f"Sending verification SMS to: {phone_number_clean} in {language}")
            
            # Generate verification code
            verification_code = generate_code()
            
            # Send SMS via Chinguisoft
            sms_result = send_sms_verification_chinguisoft(
                phone_number_clean, 
                language, 
                verification_code
            )
            
            if sms_result['success']:
                # Store the verification code in database
                if store_verification_code(phone_number_clean, verification_code):
                    return Response({
                        "message": "Code envoyé" if language == 'fr' else "تم إرسال الرمز",
                        "balance": sms_result.get('balance')
                    }, status=200)
                else:
                    return Response({
                        "error": "Failed to store verification code."
                    }, status=500)
            else:
                # Handle specific errors
                error_message = sms_result.get('error', 'Failed to send verification code')
                if 'balance' in sms_result:
                    return Response({
                        "error": error_message,
                        "balance": sms_result['balance']
                    }, status=402)  # Payment required
                elif 'Validation failed' in error_message:
                    return Response({
                        "error": "Invalid request data",
                        "details": sms_result.get('details', {})
                    }, status=422)
                elif 'Too many requests' in error_message:
                    return Response({
                        "error": "Too many requests, please try again later"
                    }, status=429)
                else:
                    return Response({
                        "error": error_message
                    }, status=500)
                    
        except Exception as e:
            print(f"Error in SendVerificationCodeView: {e}")
            return Response({
                "error": "Failed to send verification code."
            }, status=500)

class VerifyCodeView(APIView):
    def post(self, request):
        phone_number_local = request.data.get("phone_number")
        code = request.data.get("code")
        
        if not phone_number_local or not code:
            return Response({
                "error": "Phone number and code are required."
            }, status=400)
        
        # Clean phone number
        phone_number_clean = ''.join(filter(str.isdigit, phone_number_local))
        
        # Validate phone number format
        if len(phone_number_clean) != 8 or not phone_number_clean[0] in ['2', '3', '4']:
            return Response({
                "error": "Invalid phone number format."
            }, status=400)
        
        try:
            print(f"Verifying code for: {phone_number_clean}")
            
            if verify_stored_code(phone_number_clean, code):
                # Mark user as phone verified
                try:
                    user = User.objects.get(phone_number=phone_number_clean)
                    user.phone_verified = True
                    user.save()
                    print(f"User {phone_number_clean} phone verified successfully")
                except User.DoesNotExist:
                    print(f"User with phone {phone_number_clean} not found")
                
                return Response({
                    "message": "Vérification réussie"
                }, status=200)
            else:
                return Response({
                    "error": "Code invalide ou expiré"
                }, status=400)
                
        except Exception as e:
            print(f"Error in VerifyCodeView: {e}")
            return Response({
                "error": "Failed to verify code."
            }, status=500)
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count
from Citoyen.models import User, Citizen, Municipality, Admin, Problem, Complaint
from django.db import models
from django.core.serializers import serialize
import datetime
from collections import defaultdict
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.serializers import serialize
from .forms import MunicipalityForm
from Citoyen.models import Municipality

def is_superadmin(user):
    return user.user_type == "SUPERADMIN"


@login_required
@user_passes_test(is_superadmin) 
def superadmin_home(request):
    today = timezone.now().date()
    seven_days_ago = today - datetime.timedelta(days=7)
    thirty_days_ago = today - datetime.timedelta(days=30)

    # Basic Counts
    total_citizens = Citizen.objects.count()
    new_citizens_last_7_days = Citizen.objects.filter(user__date_joined__gte=seven_days_ago).count()

    total_municipalities = Municipality.objects.count()
    total_admins = Admin.objects.count()
    
    total_problems = Problem.objects.count()
    new_problems_last_7_days = Problem.objects.filter(created_at__date__gte=seven_days_ago).count()

    total_complaints = Complaint.objects.count()
    new_complaints_last_7_days = Complaint.objects.filter(created_at__date__gte=seven_days_ago).count()

    # Problem Status Breakdown
    problem_status_counts = Problem.objects.values('status').annotate(count=Count('status'))
    problem_status_data = list(problem_status_counts)
    problem_status_data_json = json.dumps(problem_status_data)

    # Complaint Status Breakdown
    complaint_status_counts = Complaint.objects.values('status').annotate(count=Count('status'))
    complaint_status_data = list(complaint_status_counts)
    complaint_status_data_json = json.dumps(complaint_status_data)

    # Recent Activities
    recent_activities = []
    
    # Recent registrations
    recent_citizens = User.objects.filter(user_type='CITIZEN').order_by('-date_joined')[:5]
    for citizen_user in recent_citizens:
        recent_activities.append({
            'text': f"Nouveau citoyen enregistre: {citizen_user.username}",
            'timestamp': citizen_user.date_joined
        })

    # Recent problems
    recent_problems = Problem.objects.order_by('-created_at')[:5]
    for problem in recent_problems:
        recent_activities.append({
            'text': f"Nouveau rapport de problème: {problem.description[:50]}...",
            'timestamp': problem.created_at
        })

    # Sort activities by timestamp
    recent_activities = sorted(recent_activities, key=lambda x: x['timestamp'], reverse=True)[:10]

    # Municipalities by problem count (last 30 days)
    municipalities_by_problems = list(Problem.objects.filter(
        created_at__date__gte=thirty_days_ago
    ).values('municipality__name').annotate(num_problems=Count('id')).order_by('-num_problems')[:5])
    
    municipalities_by_problems_json = json.dumps(municipalities_by_problems)

    context = {
        'total_citizens': total_citizens,
        'new_citizens_last_7_days': new_citizens_last_7_days,
        'total_municipalities': total_municipalities,
        'total_admins': total_admins,

        'total_problems': total_problems,
        'new_problems_last_7_days': new_problems_last_7_days,
        'problem_status_data': problem_status_data_json,
        
        'total_complaints': total_complaints,
        'new_complaints_last_7_days': new_complaints_last_7_days,
        'complaint_status_data': complaint_status_data_json,

        'recent_activities': recent_activities,
        'municipalities_by_problems': municipalities_by_problems_json
    }

    return render(request, 'super_admin/dashboard.html', context)

@login_required
def municipality_list(request):
    municipalities = Municipality.objects.all().order_by('name')
    form = MunicipalityForm()
    context = {
        'municipalities': municipalities,
        'form': form,
    }
    return render(request, 'super_admin/municipality_list.html', context)



@login_required
def municipality_create(request):
    if request.method == 'POST':
        form = MunicipalityForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'html_form': form.as_json()})
    else:  # GET Request
        form = MunicipalityForm()
        return JsonResponse({'html_form': form.as_json()})


@login_required
def municipality_update(request, pk):
    municipality = get_object_or_404(Municipality, pk=pk)
    if request.method == 'POST':
        form = MunicipalityForm(request.POST, instance=municipality)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'html_form': form.as_json()})
    else:
        form = MunicipalityForm(instance=municipality)
        return JsonResponse({'html_form': form.as_json()})

import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.core.serializers import serialize
from django.utils.translation import gettext as _
from django.middleware.csrf import get_token
from Citoyen.models import Municipality
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.serializers import serialize
from django.utils.translation import gettext as _
from Citoyen.models import Municipality  # Import your model

# NOTE: Removing the `csrf_exempt` decorators is CRUCIAL
# for proper CSRF protection with the new setup.

@login_required
def municipality_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        boundary = request.POST.get('boundary')

        errors = {}
        if not name:
            errors['name'] = [_("Ce champ est obligatoire.")]
        if not latitude:
            errors['latitude'] = [_("Ce champ est obligatoire.")]
        if not longitude:
            errors['longitude'] = [_("Ce champ est obligatoire.")]

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        try:
            Municipality.objects.create(name=name, latitude=latitude, longitude=longitude, boundary=boundary)
            return JsonResponse({'success': True})
        except Exception as e:
           # print(f"Error creating municipality: {e}")  # Log the exception for debugging
            return JsonResponse({'success': False, 'errors': {'__all__': [_("Une erreur est survenue lors de la création.")]}})
    else:  # GET request
        # Return the HTML directly for the form
        return render(request, 'super_admin/municipality_list.html', context={'create':True} )  # you return full page with static form


@login_required
def municipality_update(request, pk):
    municipality = get_object_or_404(Municipality, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        boundary = request.POST.get('boundary')

        errors = {}
        if not name:
            errors['name'] = [_("Ce champ est obligatoire.")]
        if not latitude:
            errors['latitude'] = [_("Ce champ est obligatoire.")]
        if not longitude:
            errors['longitude'] = [_("Ce champ est obligatoire.")]

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        try:
            municipality.name = name
            municipality.latitude = latitude
            municipality.longitude = longitude
            municipality.boundary = boundary
            municipality.save()
            return JsonResponse({'success': True})
        except Exception as e:
            #print(f"Error updating municipality: {e}")  # Log the exception
            return JsonResponse({'success': False, 'errors': {'__all__': [_("Une erreur est survenue lors de la modification.")]}})
    else:  # GET request
        # You might need to serialize existing data for the municipality
        # and pass it to the template for pre-filling the form if needed.
         return render(request, 'super_admin/municipality_list.html', context={'update':True, 'municipality_id':pk})  # you return full page with static form

    # Helper function removed



@login_required
def municipality_delete(request, pk):
    municipality = get_object_or_404(Municipality, pk=pk)
    if request.method == 'POST':
        try:
            municipality.delete()
            return JsonResponse({'success': True})
        except Exception as e:
             return JsonResponse({'success': False, 'errors': {'__all__': [_("Une erreur est survenue lors de la suppression.")]}})
    else: # get confirmation message
      return JsonResponse({'html_form': f'<form method="post" action="" class="js-municipality-form confirm-delete"><input type="hidden" name="id" value="{municipality.id}"><button type = "submit" class="btn btn-danger">Confirm Delete</button></form>'})


@login_required
def municipality_detail(request, pk):
    municipality = get_object_or_404(Municipality, pk=pk)
    municipality_data = {
        'id': municipality.id,
        'name': municipality.name,
        'latitude': municipality.latitude,
        'longitude': municipality.longitude,
        'boundary': municipality.boundary
    }
    return JsonResponse({'municipality': municipality_data})

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.serializers import serialize
from django.utils.translation import gettext as _
from Citoyen.models import Category


@login_required
def category_list(request):
    categories = Category.objects.all().order_by('-created_at')
    return render(request, 'super_admin/category_list.html', {'categories': categories})


@login_required
def create_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')

        errors = {}
        if not name:
            errors['name'] = [_("Ce champ est obligatoire.")]

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        try:
            category = Category.objects.create(name=name, description=description)
            return JsonResponse({'success': True, 'category': {'id': category.id, 'name': category.name, 'description': category.description}})
        except Exception as e:
            # Log the exception for debugging purposes
            return JsonResponse({'success': False, 'errors': {'__all__': [_("Une erreur s'est produite lors de la création de la catégorie.")]}})
    else:
        return render(request, 'super_admin/category_list.html', {'create':True}  ) #display static form.

@login_required
def update_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')

        errors = {}
        if not name:
            errors['name'] = [_("Ce champ est obligatoire.")]

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        try:
            category.name = name
            category.description = description
            category.save()
            return JsonResponse({'success': True, 'category': {'id': category.id, 'name': category.name, 'description': category.description}})
        except Exception as e:
            # Log the exception for debugging purposes
            return JsonResponse({'success': False, 'errors': {'__all__': [_("Une erreur s'est produite lors de la modification de la catégorie.")]}})
    else:
        return render(request, 'super_admin/category_list.html', {'update': True, 'category_id':pk})#display a static form

@login_required
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        try:
            category.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            # Log the exception for debugging purposes
            return JsonResponse({'success': False, 'errors': {'__all__': [_("Une erreur s'est produite lors de la suppression de la catégorie.")]}})
    else:#get deletion prompt
       return JsonResponse({'html_form': f'<form method="post" action="" class="js-category-form confirm-delete"><input type="hidden" name="id" value="{category.id}"><button type = "submit" class="btn btn-danger">Confirm Delete</button></form>'})
    

@login_required
def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category_data = {'id':category.id, 'name': category.name, 'description': category.description }

    return JsonResponse(category_data)

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.serializers import serialize
from django.utils.translation import gettext as _
from Citoyen.models import User, Admin, Municipality, Citizen  # Import the models

# Helper function to check if the user is a superadmin
def is_superadmin(user):
    return user.user_type == "SUPERADMIN"

@login_required
@user_passes_test(is_superadmin)  # Only Superadmins can manage admins
def admin_user_list(request):
    admins = Admin.objects.all().order_by('user__username') #order by username to show in view
    municipalities = Municipality.objects.all()
    return render(request, 'super_admin/admin_user_list.html', {'admins': admins,'municipalities':municipalities})

@login_required
@user_passes_test(is_superadmin)
def create_admin_user(request):
    if request.method == 'POST':
        email = request.POST.get('email') #email is username
        password = request.POST.get('password')
        municipality_id = request.POST.get('municipality')
        admin_title = request.POST.get('admin_title')

        errors = {}
        if not email:
            errors['email'] = [_("L'email est obligatoire.")]
        if not password:
            errors['password'] = [_("Le mot de passe est obligatoire.")]
        if not municipality_id: #if is_valid is not working or no municiaplities this line prevents failure
            errors['municipality'] = [_("La municipalité est obligatoire.")]
        # Perform checks on email, password and title
        # For simplicity, just check presence; can add email format validation later
        if errors:
            municipalities = Municipality.objects.all()
            return JsonResponse({'success': False, 'errors': errors})

        try:
            user = User.objects.create_user(email, password=password, user_type='ADMIN') #superadmin by default
            municipality = get_object_or_404(Municipality, pk=municipality_id)
            admin_profile = Admin.objects.create(user=user, municipality=municipality, admin_title=admin_title) #create Admin to profile link user-municipality
            return JsonResponse({'success': True, 'user': {'id': user.id, 'username': user.username,  'admin_title': admin_title, 'municipality': municipality.name} }) #send admin-municipality name info to JS file
        except Exception as e:
            #print(f"Error creating admin user: {e}")#log
            return JsonResponse({'success': False, 'errors': {'__all__': [_("Une erreur s'est produite lors de la création de l'administrateur.")]}})
        
    else: # is a GET
        municipalities = Municipality.objects.all()
        return render(request, 'super_admin/admin_user_list.html', {'municipalities': municipalities, 'create':True} )#the same page as view, with html forms ready to fill with datas to show or change the name of cities, and  adminUsers button called in NavBar, you must create new folder for templates here if you did not do that yet

@login_required
@user_passes_test(is_superadmin)
def update_admin_user(request, pk):
    admin_profile = get_object_or_404(Admin, pk=pk)
    if request.method == 'POST':
        email = request.POST.get('email') #email is username
        municipality_id = request.POST.get('municipality')
        admin_title = request.POST.get('admin_title')

        errors = {}
        if not email:
            errors['email'] = [_("L'email est obligatoire.")]

        # Perform checks on name, description, etc.
        if not municipality_id:
            errors['municipality'] = [_("La municipalité est obligatoire.")]
        if errors:
            municipalities = Municipality.objects.all() #load for view select input, send list errors back to view in context, with input is fill and prevent data loss
            return JsonResponse({'success': False, 'errors': errors})

        try:
            admin_profile.user.email = email #change with input form , then save info with user profile
            admin_profile.user.username = email #change with input form
            admin_profile.user.save()

            municipality = get_object_or_404(Municipality, pk=municipality_id) #then search  id, save that
            admin_profile.municipality = municipality
            admin_profile.admin_title = admin_title

            admin_profile.save()

            return JsonResponse({'success': True, 'user': {'id': admin_profile.user.id, 'username': admin_profile.user.username, 'admin_title':admin_profile.admin_title, 'municipality':municipality.name} })
        except Exception as e:
           # print(f"Error updating category: {e}")
            return JsonResponse({'success': False, 'errors': {'__all__': [_("Une erreur s'est produite lors de la modification de l'administrateur.")]}})
    else:
        municipalities = Municipality.objects.all()#load cities option if request is get
        admin_username = admin_profile.user.email
        if not admin_username:
            admin_username = admin_profile.user.username
        context = {'municipalities': municipalities, "admin_username":admin_username, 'admin_title':admin_profile.admin_title, 'admin_id':pk, 'municipality_id': admin_profile.municipality.id if admin_profile.municipality else None } #is set a select option on select list form, send old municipalities , to fill input

        return render(request, 'super_admin/admin_user_list.html', {'update': True, 'municipalities': municipalities,'admin_id': pk, "admin_username":admin_username, 'admin_title':admin_profile.admin_title, 'municipality_id': admin_profile.municipality.id if admin_profile.municipality else None } )

@login_required
@user_passes_test(is_superadmin)
def delete_admin_user(request, pk):
    admin_profile = get_object_or_404(Admin, pk=pk) #get Admin profile 
    if request.method == 'POST':
        try:

            admin_profile.user.delete() #user delete is cascase profile delete from Admin class oneToOneField relation to User Class then use
            return JsonResponse({'success': True})
        except Exception as e:
           # print(f"Error during category  delete: {e}")
            return JsonResponse({'success': False, 'errors': {'__all__': [_("Une erreur s'est produite lors de la suppression de l'administrateur.")]}})
    else:
          return JsonResponse({'html_form': f'<form method="post" action="" class="js-admin-form confirm-delete"><input type="hidden" name="id" value="{admin_profile.id}"><button type = "submit" class="btn btn-danger">Confirm Delete</button></form>'})

#New view for Citoyen
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import gettext as _
from django.db import models  # Add this import
from Citoyen.models import Citizen, Municipality  # Import your models

ITEMS_PER_PAGE = 10

@login_required
@user_passes_test(lambda u: u.user_type == "SUPERADMIN")
def citizen_user_list(request):
    search_term = request.GET.get('search', '')
    municipality_filter = request.GET.get('municipality', '') #all id on municipal table
    address_filter = request.GET.get('address', '') #get by full  name, username if you check this method

    citizens = Citizen.objects.all()

    # Apply search filter - username and full_name search name, in case no find data dispatch for user with one of many class
    if search_term:
        citizens = citizens.filter(
            models.Q(user__username__icontains=search_term) |
            models.Q(full_name__icontains=search_term) |
            models.Q(nni__icontains=search_term) #Add Name search for id, full name, part of name ...
        )

    # Apply municipality filter, in  class select input
    if municipality_filter:
        citizens = citizens.filter(municipality_id=municipality_filter)

    # Apply addres filter class
    if address_filter:
        citizens = citizens.filter(address__icontains=address_filter)
    #Order by default
    citizens = citizens.order_by('user__username') #Removed all class icon value for sort function and clean url dispatcher load

    # Paginate using numbers
    paginator = Paginator(citizens, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
#for new number value in  get dispatcher
    context = {
        'citizens': page_obj.object_list, #dispatch in table  list users
        'municipalities': Municipality.objects.all(),  #dispatch cities select for dropdownList if you add value
        'search_term': search_term, #save dispatch  value function
        'municipality_filter': municipality_filter, #city id check if one value for name dispatch number in html
        'address_filter': address_filter, #text all address for class filter
        'page_obj': page_obj, #Page objects  for class button check has_next etc
        'is_paginated': page_obj.has_other_pages(), #check if paginate value for class check all
    }

    return render(request, 'super_admin/citizen_user_list.html', context)
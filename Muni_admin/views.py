from django.shortcuts import render

# Create your views here.
def admin_home(request):
    return render(request,'muni_admin/base.html')

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils.translation import gettext as _
from django.db.models import Q, Count
from Citoyen.models import Problem,Category #Import model is core class value dispatcher name

ITEMS_PER_PAGE = 10 #You can set list value

@login_required #if value name login check view dispatcher access  for not name access
def problem_list(request):
    user_municipality = request.user.admin_profile.municipality #user by session name in model with one filter to view list is user

    search_term = request.GET.get('search', '')#dispatch all filter with names
    status_filter = request.GET.get('status', '')  #dispatch all class
    category_filter = request.GET.get('category', '')

    problems = Problem.objects.filter(municipality=user_municipality)#Load models by municipality code list

    # Apply filters
    if search_term:
         problems = problems.filter(Q(description__icontains=search_term) | #number dispatcher user in page if
                                  Q(location__icontains=search_term))# check values text

        #If used this list, be check user if it's a superadmin
    if status_filter:
        problems = problems.filter(status=status_filter)

    if category_filter:
        problems = problems.filter(category_id=category_filter)


    # Pagination use in load last line
    paginator = Paginator(problems, ITEMS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    # all new name to load template list by name in order
    context = {
        'problems': page_obj,
        'search_term': search_term,  # value  filter text dispatcher number

       'status_filter': status_filter, #dispatcher name chart

        'category_filter': category_filter,# if used set code values
        'categories': Category.objects.all(),#select option id name function list
        'status_choices': Problem.STATUS_CHOICES,  #model list for select dropdownMenu  class options value
         #all names and dispatcher for template list class, and dispatcher function list
    }

    return render(request, 'muni_admin/problem_list.html', context)
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Avg, F, ExpressionWrapper, fields, Q
from django.core import serializers
from Citoyen.models import Problem, Complaint, Category, StatusLog
import datetime
from collections import defaultdict
import json

@login_required
def dashboard(request):
    municipality = request.user.admin_profile.municipality
    
    # Get period parameter (default: 7 days)
    days_period = int(request.GET.get('days', 7))
    today = timezone.now().date()
    period_start = today - datetime.timedelta(days=days_period)
    previous_period_start = period_start - datetime.timedelta(days=days_period)
    
    # Basic counts
    total_problems = Problem.objects.filter(municipality=municipality).count()
    new_problems_last_period = Problem.objects.filter(
        municipality=municipality, 
        created_at__date__gte=period_start
    ).count()
    
    # Compare with previous period
    problems_previous_period = Problem.objects.filter(
        municipality=municipality,
        created_at__date__gte=previous_period_start,
        created_at__date__lt=period_start
    ).count()
    
    # Calculate percent change
    problem_percent_change = 0
    if problems_previous_period > 0:
        problem_percent_change = round(((new_problems_last_period - problems_previous_period) / problems_previous_period) * 100)
    
    # Same for complaints
    total_complaints = Complaint.objects.filter(municipality=municipality).count()
    new_complaints_last_period = Complaint.objects.filter(
        municipality=municipality, 
        created_at__date__gte=period_start
    ).count()
    
    complaints_previous_period = Complaint.objects.filter(
        municipality=municipality,
        created_at__date__gte=previous_period_start,
        created_at__date__lt=period_start
    ).count()
    
    complaint_percent_change = 0
    if complaints_previous_period > 0:
        complaint_percent_change = round(((new_complaints_last_period - complaints_previous_period) / complaints_previous_period) * 100)
    
    # New problems percent change
    new_problem_percent_change = 0
    if problems_previous_period > 0:
        new_problem_percent_change = round(((new_problems_last_period - problems_previous_period) / problems_previous_period) * 100)
    
    # New complaints percent change
    new_complaint_percent_change = 0
    if complaints_previous_period > 0:
        new_complaint_percent_change = round(((new_complaints_last_period - complaints_previous_period) / complaints_previous_period) * 100)
    
    # Status breakdown for problems
    problem_status_data = Problem.objects.filter(
        municipality=municipality
    ).values('status').annotate(count=Count('status'))
    
    # Status breakdown for complaints
    complaint_status_data = Complaint.objects.filter(
        municipality=municipality
    ).values('status').annotate(count=Count('status'))
    
    # Top problem categories
    problem_categories_data = Problem.objects.filter(
        municipality=municipality
    ).values('category__name').annotate(
        count=Count('category')
    ).order_by('-count')[:5]
    
    # Problem and complaint time series data (for the charts)
    # Get data for last X days
    time_series_days = 90  # Show data for last 90 days
    time_series_start = today - datetime.timedelta(days=time_series_days)
    
    # Generate date range
    date_range = []
    current_date = time_series_start
    while current_date <= today:
        date_range.append(current_date)
        current_date += datetime.timedelta(days=1)
    
    # Problems by day
    problems_by_day = Problem.objects.filter(
        municipality=municipality, 
        created_at__date__gte=time_series_start
    ).annotate(
        created_day=ExpressionWrapper(
            F('created_at__date'), 
            output_field=fields.DateField()
        )
    ).values('created_day').annotate(
        count=Count('id')
    ).order_by('created_day')
    
    # Convert to dictionary for easier lookup
    problems_data = defaultdict(int)
    for item in problems_by_day:
        problems_data[item['created_day'].strftime('%Y-%m-%d')] = item['count']
    
    # Complaints by day
    complaints_by_day = Complaint.objects.filter(
        municipality=municipality, 
        created_at__date__gte=time_series_start
    ).annotate(
        created_day=ExpressionWrapper(
            F('created_at__date'), 
            output_field=fields.DateField()
        )
    ).values('created_day').annotate(
        count=Count('id')
    ).order_by('created_day')
    
    complaints_data = defaultdict(int)
    for item in complaints_by_day:
        complaints_data[item['created_day'].strftime('%Y-%m-%d')] = item['count']
    
    # Prepare time series data for charts
    problems_time_series = {
        'dates': [d.strftime('%Y-%m-%d') for d in date_range],
        'series': [{
            'name': 'Problèmes',
            'data': [problems_data.get(d.strftime('%Y-%m-%d'), 0) for d in date_range]
        }]
    }
    
    complaints_time_series = {
        'dates': [d.strftime('%Y-%m-%d') for d in date_range],
        'series': [{
            'name': 'Réclamations',
            'data': [complaints_data.get(d.strftime('%Y-%m-%d'), 0) for d in date_range]
        }]
    }
    
    # Resolution time data
    # Calculate average time to resolve by category
    # First, get problems that have been resolved
    resolved_problems = Problem.objects.filter(
        municipality=municipality,
        status='RESOLVED'
    )
    
    # Group them by category and calculate average resolution time
    resolution_time_data = []
    
    # Get status logs for resolved problems
    if resolved_problems.exists():
        status_logs = StatusLog.objects.filter(
            record_type='PROBLEM',
            record_id__in=resolved_problems.values_list('id', flat=True),
            new_status='RESOLVED'
        )
        
        # Group by category
        category_resolution_times = defaultdict(list)
        
        for problem in resolved_problems:
            # Find the log entry where this problem was resolved
            log_entry = status_logs.filter(record_id=problem.id).first()
            
            if log_entry:
                # Calculate time difference in days
                resolution_time = (log_entry.changed_at.date() - problem.created_at.date()).days
                category_name = problem.category.name if problem.category else 'Sans catégorie'
                category_resolution_times[category_name].append(resolution_time)
        
        # Calculate averages
        for category, times in category_resolution_times.items():
            if times:
                avg_days = sum(times) / len(times)
                resolution_time_data.append({
                    'category': category,
                    'avg_days': avg_days
                })
    
    # Sort by average resolution time (ascending)
    resolution_time_data.sort(key=lambda x: x['avg_days'])
    
    # Get problem locations for the map
    problem_map_data = Problem.objects.filter(
        municipality=municipality
    ).select_related('category').values(
        'pk', 'latitude', 'longitude', 'description', 'status', 
        'created_at', 'category__name'
    )
    
    # Enhanced recent activities with more detail
    recent_activities = []
    
    # Recent problems with more detailed info
    recent_problems = Problem.objects.filter(
        municipality=municipality
    ).select_related('category', 'citizen').order_by('-created_at')[:10]
    
    for problem in recent_problems:
        status_display = dict(Problem.STATUS_CHOICES).get(problem.status, problem.status)
        detail_url = f"/admin/problems/{problem.id}/detail/"
        
        recent_activities.append({
            'type': 'problem',
            'text': f"Problème signalé: {problem.description[:50]}...",
            'timestamp': problem.created_at,
            'status': problem.status,
            'status_display': status_display,
            'detail_url': detail_url
        })
    
    # Recent complaints with more detailed info
    recent_complaints = Complaint.objects.filter(
        municipality=municipality
    ).select_related('citizen').order_by('-created_at')[:10]
    
    for complaint in recent_complaints:
        status_display = dict(Complaint.STATUS_CHOICES).get(complaint.status, complaint.status)
        detail_url = f"/admin/complaints/{complaint.id}/detail/"
        
        recent_activities.append({
            'type': 'complaint',
            'text': f"Réclamation soumise: {complaint.subject[:50]}...",
            'timestamp': complaint.created_at,
            'status': complaint.status,
            'status_display': status_display,
            'detail_url': detail_url
        })
    
    # Sort recent activities by timestamp
    recent_activities = sorted(recent_activities, key=lambda x: x['timestamp'], reverse=True)[:15]
    
    # Serialize data for JavaScript
    problem_status_data_dump = json.dumps(list(problem_status_data))
    complaint_status_data_dump = json.dumps(list(complaint_status_data))
    problem_categories_data_dump = json.dumps( list(problem_categories_data))
    problem_map_data_dump = json.dumps(list(problem_map_data), default=str)
    
    # Context for the template
    context = {
        'total_problems': total_problems,
        'new_problems_last_7_days': new_problems_last_period,
        'problem_percent_change': problem_percent_change,
        'new_problem_percent_change': new_problem_percent_change,
        
        'total_complaints': total_complaints,
        'new_complaints_last_7_days': new_complaints_last_period,
        'complaint_percent_change': complaint_percent_change,
        'new_complaint_percent_change': new_complaint_percent_change,
        
        'problem_status_data': problem_status_data_dump,
        'complaint_status_data': complaint_status_data_dump,
        'problem_categories_data': problem_categories_data_dump,
        'problems_time_series': json.dumps(problems_time_series),
        'complaints_time_series': json.dumps(complaints_time_series),
        'resolution_time_data': json.dumps(resolution_time_data),
        'problem_map_data': problem_map_data_dump,
        
        'recent_activities': recent_activities,
        'municipality': municipality,
        'navName': 'dashboard',
    }
    
    return render(request, 'muni_admin/dashboard.html', context)


from django.shortcuts import get_object_or_404
from Citoyen.models import Problem, StatusLog # Assuming models are in Citoyen app
from Citoyen.models import Notification
@login_required
def problem_detail(request, problem_id):
    # Fetch the specific problem, ensuring it belongs to the admin's municipality (or handle superadmin case)
    problem = get_object_or_404(Problem.objects.select_related(
        'citizen', 'category', 'municipality'
    ), pk=problem_id, municipality=request.user.admin_profile.municipality)
    
    # Fetch status change history for this problem
    status_logs = StatusLog.objects.filter(
        record_type='PROBLEM', 
        record_id=problem.id
    ).order_by('-changed_at').select_related('changed_by')
    
    # Handle status update form submission
    if request.method == 'POST':
        old_status = problem.status
        new_status = request.POST.get('status')
        comment = request.POST.get('comment', '')
        
        if new_status and new_status != old_status:
            # Update problem status
            problem.status = new_status
            problem.comment = comment
            problem.save()
            
            # Create status log entry
            StatusLog.objects.create(
                record_type='PROBLEM',
                record_id=problem.id,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user,
                changed_at=timezone.now()
            )
            
            # Optional: Create notification for the citizen
            Notification.objects.create(
                user=problem.citizen.user,
                title=_("Mise à jour de votre signalement"),
                message=_("Le statut de votre problème a été mis à jour à: {}").format(
                    dict(Problem.STATUS_CHOICES)[new_status]
                ),
                type='PROBLEM_UPDATE',
                related_id=str(problem.id),
                related_type='PROBLEM'
            )
            
            # Add success message
            from django.contrib import messages
            messages.success(request, _("Statut mis à jour avec succès."))
            
            # Redirect to avoid form resubmission
            from django.shortcuts import redirect
            return redirect('Muni_admin:problem_detail', problem_id=problem_id)
    
    # Prepare context for the template
    context = {
        'problem': problem,
        'status_logs': status_logs,
        'status_choices': Problem.STATUS_CHOICES,  # Pass status choices for potential status change form
        'navName': 'problems',  # For navigation highlighting
    }
    
    return render(request, 'muni_admin/problem_detail.html', context)


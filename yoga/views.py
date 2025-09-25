from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate , logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, ProfileForm, PracticeForm
from .models import Pose, Practice
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils import timezone
from datetime import timedelta
import calendar
from datetime import date, datetime

def landing(request):
    top_poses = Pose.objects.all()[:4]
    return render(request, 'yoga/landing.html', {'top_poses': top_poses})

def poses_view(request):
    poses = Pose.objects.all()[:8]  # show first 8
    return render(request, 'yoga/poses.html', {'poses': poses})



def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # create profile
            from .models import Profile
            Profile.objects.create(user=user)
            login(request, user)
            return redirect('yoga:profile')
    else:
        form = SignUpForm()
    return render(request, 'yoga/signup.html', {'form': form})

from django.contrib.auth.views import LoginView, LogoutView
class CustomLoginView(LoginView):
    template_name = 'yoga/login.html'

@login_required
# views.py
def profile_view(request):
    profile = request.user.profile

    # full queryset for logic
    practices_qs = request.user.practices.all()

    # slice only for display if you need
    practices = practices_qs[:30]

    # collect distinct days practiced
    practiced_days = set(practices_qs.values_list("date", flat=True))

    practice_form = PracticeForm()

     # Get month/year from query params or use current
    month = int(request.GET.get("month", date.today().month))
    year = int(request.GET.get("year", date.today().year))
    today = date.today()

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.itermonthdates(year, month)

    # Calendar setup
    calendar_days = []
    for day in month_days:
        calendar_days.append({
            "label": day.day,
            "in_month": day.month == month,
            "practiced": day in practiced_days and day <= today,
            "is_today": day == today,
            "future": day > today,
        })

    # Previous / next month for navigation
    first_day = date(year, month, 1)
    prev_month = first_day - timedelta(days=1)
    next_month = (first_day + timedelta(days=31)).replace(day=1)

    return render(request, "yoga/profile.html", {
        "profile": profile,
        "practices": practices[:30],
        "practice_form": practice_form,
        "calendar_days": calendar_days,
        "month_name": first_day.strftime("%B"),
        "year": year,
        "prev_month": prev_month,
        "next_month": next_month,
    })


def edit_profile_view(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('yoga:profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'yoga/edit_profile.html', {
        'form': form
    })

@login_required
def add_practice(request):
    if request.method == 'POST':
        form = PracticeForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.user = request.user
            p.save()
            form.save_m2m()
            return redirect('yoga:profile')
    return redirect('yoga:profile')

@login_required
def stats_view(request):
    user = request.user
    practices = user.practices.all()
    total_days = practices.count()
    total_minutes = sum([p.duration_minutes for p in practices])
    # simple weekly last-7 days breakdown
    today = timezone.localdate()
    last7 = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    breakdown = []
    for d in last7:
        exists = practices.filter(date=d).exists()
        breakdown.append({'date': d.isoformat(), 'done': exists})
    return render(request, 'yoga/stats.html', {
        'total_days': total_days,
        'total_minutes': total_minutes,
        'breakdown': breakdown
    })

# JSON endpoint for calendar to fetch practice dates
@login_required
@require_GET
def practice_dates_json(request):
    dates = list(request.user.practices.values_list('date', flat=True))
    # convert to ISO string list
    iso_dates = [d.isoformat() for d in dates]
    return JsonResponse({'dates': iso_dates})


@login_required
def session_view(request):
    return render(request, "yoga/session.html")


@login_required
def custom_logout(request):
    logout(request)
    return redirect('yoga:landing')


# def poses(request):
#     poses = [
#         {"name": "Mountain Pose", "difficulty": "Beginner", "duration": "30s", "image": "🏔️"},
#         {"name": "Warrior I", "difficulty": "Intermediate", "duration": "45s", "image": "🗡️"},
#         {"name": "Tree Pose", "difficulty": "Beginner", "duration": "60s", "image": "🌳"},
#         {"name": "Downward Dog", "difficulty": "Beginner", "duration": "45s", "image": "🐕"},
#         {"name": "Cobra Pose", "difficulty": "Intermediate", "duration": "30s", "image": "🐍"},
#         {"name": "Warrior III", "difficulty": "Advanced", "duration": "45s", "image": "⚔️"},
#     ]
#     return render(request, "yoga/poses.html", {"poses": poses})
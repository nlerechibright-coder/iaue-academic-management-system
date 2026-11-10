# academics/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AcademicSession, Semester

def is_management(user):
    return hasattr(user, 'is_management') and user.is_management

@login_required
def session_list(request):
    if not is_management(request.user):
        return redirect('login')
    
    sessions = AcademicSession.objects.all().order_by('-name')
    return render(request, 'academics/session_list.html', {'sessions': sessions})

@login_required
def session_create(request):
    if not is_management(request.user):
        return redirect('login')
    
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        if not name:
            messages.error(request, "Session Name is required.")
            return render(request, 'academics/session_form.html', {})

        if AcademicSession.objects.filter(name=name).exists():
            messages.error(request, f"Session '{name}' already exists.")
            return render(request, 'academics/session_form.html', {})

        try:
            AcademicSession.objects.create(
                name=name,
                start_date=start_date or None,
                end_date=end_date or None,
                is_active=False
            )
            messages.success(request, f"Academic Session '{name}' created.")
            return redirect('academics:session_list')
        except Exception as e:
            messages.error(request, f"Error creating session: {str(e)}")
            
    return render(request, 'academics/session_form.html')

@login_required
def session_edit(request, pk):
    """Handles editing an existing academic session."""
    if not is_management(request.user):
        return redirect('login')
    
    session = get_object_or_404(AcademicSession, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_active = request.POST.get('is_active') == 'on'
        
        if not name:
            messages.error(request, "Session Name is required.")
            return render(request, 'academics/session_form.html', {'session': session})

        # Check uniqueness excluding current instance
        if AcademicSession.objects.filter(name=name).exclude(pk=pk).exists():
            messages.error(request, "Another session with this name exists.")
            return render(request, 'academics/session_form.html', {'session': session})

        session.name = name
        session.start_date = start_date or None
        session.end_date = end_date or None
        session.is_active = is_active
        session.save()
        
        messages.success(request, f"Session '{name}' updated.")
        return redirect('academics:session_list')
        
    return render(request, 'academics/session_form.html', {'session': session})

@login_required
def semester_list(request):
    if not is_management(request.user):
        return redirect('login')
    
    semesters = Semester.objects.select_related('session').all().order_by('-session__name', 'name')
    return render(request, 'academics/semester_list.html', {'semesters': semesters})

@login_required
def semester_create(request):
    if not is_management(request.user):
        return redirect('login')
    
    if request.method == 'POST':
        session_id = request.POST.get('session')
        name = request.POST.get('name') # FIRST or SECOND
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        try:
            sess = AcademicSession.objects.get(id=session_id)
            
            if Semester.objects.filter(session=sess, name=name).exists():
                messages.error(request, f"{name} semester already exists for {sess.name}.")
                return render(request, 'academics/semester_form.html', {'sessions': AcademicSession.objects.all()})

            Semester.objects.create(
                session=sess,
                name=name,
                start_date=start_date or None,
                end_date=end_date or None,
                is_active=False
            )
            messages.success(request, f"Semester '{name}' created for {sess.name}.")
            return redirect('academics:semester_list')
            
        except AcademicSession.DoesNotExist:
            messages.error(request, "Invalid Session selected.")
            
    sessions = AcademicSession.objects.all()
    return render(request, 'academics/semester_form.html', {'sessions': sessions})
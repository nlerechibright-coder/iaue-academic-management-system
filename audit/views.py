from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from approvals.models import ApprovalAction


def is_management(user):
    return hasattr(user, 'is_management') and user.is_management


@login_required
def activity_list(request):
    if not is_management(request.user):
        messages.error(request, 'Access Denied.')
        return redirect('login')

    activities = ApprovalAction.objects.select_related(
        'actor',
        'result_sheet__offering__course',
    ).order_by('-timestamp')[:50]

    return render(request, 'audit/activity_list.html', {'activities': activities})

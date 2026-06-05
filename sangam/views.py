from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Sum

from .models import Group, Session, Transaction, Record, ActivityLog
from payments.models import Payment
from accounts.models import User
from sangam.services.activity_service import log_activity


# =========================================
# DASHBOARD
# =========================================

@login_required
def dashboard(request):

    group = Group.objects.first()
    active_session = Session.objects.filter(status='open').first()

    users = User.objects.filter(is_active=True).order_by('name')
    total_members = users.count()

    transactions = Transaction.objects.all().order_by('-created_at')[:10]

    total_investment = Transaction.objects.filter(
        type='investment'
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_fine = Transaction.objects.filter(
        type='fine'
    ).aggregate(total=Sum('amount'))['total'] or 0

    collected_amount = total_investment
    group_balance = total_investment + total_fine

    weekly_amount = group.weekly_amount if group else 0

    closed_sessions = Session.objects.filter(
        group=group, status='closed'
    ) if group else Session.objects.none()

    past_expected = closed_sessions.count() * weekly_amount

    members_preview = []

    for user in users:
        fine_amount = 0
        current_status = 'pending'

        if active_session:
            record = Record.objects.filter(
                user=user, session=active_session
            ).first()
            if record:
                current_status = record.status
                fine_amount = record.fine

        past_fines = Record.objects.filter(
            user=user, session__in=closed_sessions
        ).aggregate(total=Sum('fine'))['total'] or 0

        past_paid = Payment.objects.filter(
            user=user, session__in=closed_sessions
        ).aggregate(total=Sum('total_paid'))['total'] or 0

        previous_due = max(0, (past_expected + past_fines) - past_paid)

        current_payment = None
        if active_session:
            current_payment = Payment.objects.filter(
                user=user, session=active_session
            ).first()

        amount_paid = current_payment.total_paid if current_payment else 0
        amount_due = previous_due + weekly_amount + fine_amount
        paid = amount_paid >= amount_due

        members_preview.append({
            'id': user.id,
            'name': user.name,
            'phone': user.phone,
            'role': user.role,
            'status': current_status,
            'weekly_amount': weekly_amount,
            'fine_amount': fine_amount,
            'previous_due': previous_due,
            'amount_due': amount_due,
            'amount_paid': amount_paid,
            'paid': paid,
        })

    expected_collection = (group.weekly_amount * total_members) if group else 0
    pending_amount = max(0, expected_collection - collected_amount)

    collection_progress = 0
    if expected_collection > 0:
        collection_progress = min(
            100, round((collected_amount / expected_collection) * 100, 1)
        )

    present_count = late_count = absent_count = 0
    if active_session:
        present_count = Record.objects.filter(session=active_session, status='present').count()
        late_count = Record.objects.filter(session=active_session, status='late').count()
        absent_count = Record.objects.filter(session=active_session, status='absent').count()

    context = {
        'group': group,
        'total_members': total_members,
        'transactions': transactions,
        'total_investment': total_investment,
        'total_fine': total_fine,
        'active_session': active_session,
        'collected_amount': collected_amount,
        'pending_amount': pending_amount,
        'group_balance': group_balance,
        'members_preview': members_preview,
        'expected_collection': expected_collection,
        'collection_progress': collection_progress,
        'present_count': present_count,
        'late_count': late_count,
        'absent_count': absent_count,
    }

    return render(request, 'sangam/dashboard.html', context)


# =========================================
# MEMBER DETAIL  (fully rewritten)
# =========================================

@login_required
def member_detail(request, user_id):
    member = get_object_or_404(User, id=user_id)
    group = Group.objects.first()

    # All transactions for this member
    transactions = Transaction.objects.filter(
        user=member
    ).select_related('session').order_by('-created_at')

    total_paid = transactions.filter(
        type='investment'
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_fines = transactions.filter(
        type='fine'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # All attendance records
    all_records = Record.objects.filter(
        user=member
    ).select_related('session').order_by('-session__date')

    total_sessions = all_records.count()
    present_count = all_records.filter(status='present').count()
    late_count = all_records.filter(status='late').count()
    absent_count = all_records.filter(status='absent').count()

    attendance_rate = 0
    if total_sessions > 0:
        attendance_rate = round(
            ((present_count + late_count) / total_sessions) * 100, 1
        )

    # Absent/late records with fines
    absent_records = all_records.filter(
        status__in=['absent', 'late']
    ).order_by('-session__date')

    # Session-by-session breakdown
    closed_sessions = Session.objects.filter(
        group=group, status='closed'
    ).order_by('-date') if group else Session.objects.none()

    weekly_amount = group.weekly_amount if group else 0

    session_records = []
    for session in closed_sessions:
        record = Record.objects.filter(user=member, session=session).first()
        payment = Payment.objects.filter(user=member, session=session).first()
        amount_paid = payment.total_paid if payment else 0
        due = weekly_amount + (record.fine if record else 0)
        session_records.append({
            'date': session.date,
            'status': record.status if record else '—',
            'fine': record.fine if record else 0,
            'amount_paid': amount_paid,
            'paid': amount_paid >= due,
        })

    # Calculate pending due
    past_fines_total = all_records.filter(
        session__status='closed'
    ).aggregate(total=Sum('fine'))['total'] or 0

    past_paid_total = Payment.objects.filter(
        user=member,
        session__status='closed'
    ).aggregate(total=Sum('total_paid'))['total'] or 0

    expected_total = closed_sessions.count() * weekly_amount
    pending_due = max(0, (expected_total + past_fines_total) - past_paid_total)

    context = {
        'member': member,
        'transactions': transactions,
        'total_paid': total_paid,
        'total_fines': total_fines,
        'pending_due': pending_due,
        'total_sessions': total_sessions,
        'present_count': present_count,
        'late_count': late_count,
        'absent_count': absent_count,
        'attendance_rate': attendance_rate,
        'absent_records': absent_records,
        'session_records': session_records,
    }

    return render(request, 'sangam/member_detail.html', context)


# =========================================
# GROUP SETTINGS
# =========================================

@login_required
def group_settings(request):

    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('dashboard')

    group = Group.objects.first()
    users = User.objects.filter(is_active=True).order_by('name')

    if not group:
        group = Group.objects.create(
            name='My Sangam',
            meeting_day='Sunday',
            start_time='21:00',
            end_time='22:00',
            weekly_amount=0,
            late_fine=0,
            absent_fine=0,
        )

    if request.method == 'POST':
        group.name = request.POST.get('name', group.name)
        group.description = request.POST.get('description', '')
        group.max_members = int(request.POST.get('max_members') or 50)
        group.weekly_amount = float(request.POST.get('weekly_amount') or 0)
        group.increment_amount = float(request.POST.get('increment_amount') or 0)
        group.late_fine = float(request.POST.get('late_fine') or 0)
        group.absent_fine = float(request.POST.get('absent_fine') or 0)
        group.meeting_day = request.POST.get('meeting_day', group.meeting_day)
        group.start_time = request.POST.get('start_time', group.start_time)
        group.end_time = request.POST.get('end_time') or group.end_time
        group.reminder_enabled = bool(request.POST.get('reminder_enabled'))
        group.save()

        log_activity(
            request.user, 'group',
            f"Updated group settings for {group.name}"
        )
        return redirect('dashboard')

    return render(request, 'sangam/group_settings.html', {
        'group': group,
        'users': users,
    })


# =========================================
# ADD MEMBER
# =========================================

@login_required
def add_member(request):

    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('dashboard')

    if request.method == 'POST':
        User.objects.create_user(
            username=request.POST.get('username'),
            phone=request.POST.get('phone'),
            password=request.POST.get('password'),
            name=request.POST.get('name'),
            role='member',
        )
        log_activity(
            request.user, 'member',
            f"Added new member: {request.POST.get('name')}"
        )
        return redirect('group_settings')

    return render(request, 'sangam/add_member.html')


# =========================================
# MAKE ADMIN
# =========================================

@login_required
def make_admin(request, user_id):

    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id)
    user.role = 'admin'
    user.save()

    log_activity(
        request.user, 'member',
        f"Promoted {user.name} to admin"
    )
    return redirect('group_settings')


# =========================================
# REMOVE ADMIN
# =========================================

@login_required
def remove_admin(request, user_id):

    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('dashboard')

    if request.user.id == user_id:
        return HttpResponse("⚠️ You cannot remove your own admin rights.")

    user = get_object_or_404(User, id=user_id)
    user.role = 'member'
    user.save()

    log_activity(
        request.user, 'member',
        f"Removed admin rights from {user.name}"
    )
    return redirect('group_settings')


# =========================================
# START SESSION
# =========================================

@login_required
def start_session(request):

    if request.user.role != 'admin' and not request.user.is_staff:
        return HttpResponse('Unauthorized')

    group = Group.objects.first()
    if not group:
        return HttpResponse('⚠️ No Sangam group found.')

    if Session.objects.filter(status='open').exists():
        return HttpResponse('⚠️ A session is already active.')

    session = Session.objects.create(
        group=group,
        date=timezone.now().date(),
        start_datetime=timezone.now(),
        status='open',
    )

    # Pre-create records for all active members
    for user in User.objects.filter(is_active=True):
        Record.objects.get_or_create(
            session=session,
            user=user,
            defaults={'status': 'present', 'fine': 0},
        )

    log_activity(
        request.user, 'session',
        f"Started new session for {group.name}"
    )
    return redirect('dashboard')


# =========================================
# END SESSION (abort without saving)
# =========================================

@login_required
def end_session(request):

    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('dashboard')

    session = Session.objects.filter(status='open').first()
    if session:
        session.status = 'closed'
        session.end_datetime = timezone.now()
        session.save()

    log_activity(
        request.user, 'session',
        f"Aborted session {session.id if session else 'unknown'}"
    )
    return redirect('dashboard')


# =========================================
# SAVE AND CLOSE SESSION
# =========================================

@login_required
def save_and_close_session(request):

    if request.user.role != 'admin' and not request.user.is_staff:
        return redirect('dashboard')

    session = Session.objects.filter(status='open').first()
    if not session:
        return redirect('dashboard')

    group = session.group
    members = User.objects.filter(is_active=True)

    for member in members:
        status = request.POST.get(f'status_{member.id}', 'present')
        amount = float(request.POST.get(f'amount_{member.id}', 0) or 0)
        paid_checked = bool(request.POST.get(f'paid_{member.id}'))

        fine = 0
        if status == 'late':
            fine = group.late_fine
        elif status == 'absent':
            fine = group.absent_fine

        # Update attendance record
        record = Record.objects.filter(
            session=session, user=member
        ).first()
        if record:
            record.status = status
            record.fine = fine
            record.save()
        else:
            Record.objects.create(
                session=session, user=member,
                status=status, fine=fine
            )

        # Record payment
        Payment.objects.update_or_create(
            user=member,
            session=session,
            defaults={
                'amount': amount,
                'fine_paid': fine,
                'total_paid': amount,
            }
        )

        # Investment transaction (only if amount > 0)
        if amount > 0:
            Transaction.objects.create(
                user=member, session=session,
                amount=amount, type='investment'
            )

        # Fine transaction (only if fine > 0)
        if fine > 0:
            Transaction.objects.create(
                user=member, session=session,
                amount=fine, type='fine'
            )

    session.status = 'closed'
    session.end_datetime = timezone.now()
    session.save()

    log_activity(
        request.user, 'session',
        f"Saved and closed session {session.id}"
    )
    return redirect('dashboard')


# =========================================
# WELCOME
# =========================================

def welcome(request):
    return render(request, 'sangam/welcome.html')


# =========================================
# MARK ATTENDANCE (manual single record)
# =========================================

@login_required
def mark_attendance(request, record_id):

    record = get_object_or_404(Record, id=record_id)
    group = record.session.group
    current_hour = timezone.now().hour

    if current_hour <= 21:
        record.status = 'present'
        record.fine = 0
    elif current_hour <= 22:
        record.status = 'late'
        record.fine = group.late_fine
    else:
        record.status = 'absent'
        absent_count = Record.objects.filter(
            user=record.user, status='absent'
        ).count()
        record.fine = group.absent_fine + (absent_count * getattr(group, 'absent_increment', 0))

    record.save()

    if record.fine > 0:
        Transaction.objects.create(
            user=record.user,
            session=record.session,
            amount=record.fine,
            type='fine'
        )

    return redirect('dashboard')
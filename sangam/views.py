from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Session, Transaction, Group, Record
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.http import HttpResponse
from sangam.services.fine_service import calculate_fine
from accounts.models import User



@login_required
def dashboard(request):
    users = User.objects.all()
    sessions = Session.objects.all().order_by('-date')[:5]
    transactions = Transaction.objects.all().order_by('-created_at')[:10]

    total_members = users.count()
    total_investment = sum(t.amount for t in transactions if t.type == 'investment')
    total_fine = sum(t.amount for t in transactions if t.type == 'fine')
    active_session = Session.objects.filter(status='open').first()
    session = Session.objects.filter(status='open').first()

    return render(request, 'sangam/dashboard.html', {
        'users': users,
        'sessions': sessions,
        'transactions': transactions,
        'total_members': total_members,
        'total_investment': total_investment,
        'total_fine': total_fine,
        'active_session': active_session
    })
    
    


def make_admin(request, user_id):
    if request.user.role != 'admin':
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id)
    user.role = 'admin'
    user.save()

    return redirect('dashboard')


def remove_admin(request, user_id):
    if request.user.role != 'admin':
        return redirect('dashboard')
    if request.user.id == user_id:
        return HttpResponse("⚠️ You cannot remove your own admin rights")
    user = get_object_or_404(User, id=user_id)
    user.role = 'member'
    user.save()

    return redirect('dashboard')



def add_member(request):

    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        role = request.POST.get('role')

        if User.objects.filter(phone=phone).exists():
            return HttpResponse("User already exists")

        User.objects.create(
            name=name,
            phone=phone,
            password=make_password(password),
            role=role
        )

        return redirect('dashboard')

    return render(request, 'sangam/add_member.html')
# ========================

# ========================
# passbook


# =========================
# SESSION MANAGEMENT

@login_required
def start_session(request):

    if request.user.role != 'admin':
        return HttpResponse("Unauthorized")

    # 🔴 Get group
    group = Group.objects.first()

    # 🔴 STOP execution if no group
    if group is None:
        return HttpResponse("⚠️ No Sangam group found. Create one in admin panel.")

    # 🔴 Prevent multiple sessions
    if Session.objects.filter(status='open').exists():
        return HttpResponse("⚠️ Session already active")

    # ✅ Safe creation
    Session.objects.create(
        group=group,
        date=timezone.now().date(),
        start_datetime=timezone.now(),
        status='open'
    )

    return redirect('dashboard')

@login_required
def end_session(request):
    if request.user.role != 'admin':
        return redirect('dashboard')

    session = Session.objects.filter(status='open').first()

    if session:
        session.status = 'closed'
        session.end_datetime = timezone.now()
        session.save()

    return redirect('dashboard')


@login_required
def mark_attendance(request, record_id):
    record = Record.objects.get(id=record_id)

    current_hour = timezone.now().hour

    if current_hour <= 21:
        record.status = 'present'
        record.fine = 0
    elif current_hour <= 22:
        record.status = 'late'
        record.fine = record.session.group.late_fine
    else:
        record.status = 'absent'
        record.fine = record.session.group.late_fine * 2

    record.save()
    return redirect('dashboard')


@login_required
def add_payment(request, record_id):
    record = Record.objects.get(id=record_id)

    amount = float(request.POST.get('amount', 0))

    record.amount_paid += amount
    record.paid = True
    record.save()

    Transaction.objects.create(
        user=record.user,
        session=record.session,
        amount=amount,
        type='investment'
    )

    return redirect('dashboard')



def members_payble(request, record_id):
    record = Record.objects.get(id=record_id)

    fine = calculate_fine(record)

    return HttpResponse(f"Amount payable by {record.user.name}: ₹{fine}")

def member_details(request, user_id):
    user = get_object_or_404(User, id=user_id)
    transactions = Transaction.objects.filter(user=user).order_by('-created_at')

    total_investment = sum(t.amount for t in transactions if t.type == 'investment')
    total_fine = sum(t.amount for t in transactions if t.type == 'fine')

    balance = total_investment - total_fine

    return render(request, 'sangam/member_details.html', {
        'user': user,
        'transactions': transactions,
        'total_investment': total_investment,
        'total_fine': total_fine,
        'balance': balance
    })


def welcome(request):
    return render(request, 'sangam/welcome.html')
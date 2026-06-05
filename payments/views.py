from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone

from .models import Payment
from sangam.models import Group, Session, Record, Transaction
from accounts.models import User


# =========================================
# PAYMENT LEDGER
# =========================================

@login_required
def payment_ledger(request):

    group = Group.objects.first()

    if not group:
        return render(request, "payments/payment_ledger.html", {
            "members": [], "group": None,
        })

    active_session = Session.objects.filter(
        group=group, status="open"
    ).first()

    users = User.objects.filter(is_active=True).order_by("name")

    # All closed sessions for calculating past dues
    closed_sessions = Session.objects.filter(group=group, status="closed")
    weekly_amount = group.weekly_amount
    past_sessions_count = closed_sessions.count()

    members = []
    total_expected = 0
    total_collected = 0
    total_fines = 0
    total_pending = 0

    for user in users:

        # --- Current session data ---
        record = None
        current_payment = None
        fine_amount = 0
        current_amount_paid = 0

        if active_session:
            record = Record.objects.filter(
                user=user, session=active_session
            ).first()
            current_payment = Payment.objects.filter(
                user=user, session=active_session
            ).first()

        attendance_status = record.status if record else "pending"
        fine_amount = record.fine if record else 0
        current_amount_paid = current_payment.total_paid if current_payment else 0

        # --- Past dues calculation ---
        past_fines = Record.objects.filter(
            user=user, session__in=closed_sessions
        ).aggregate(total=Sum("fine"))["total"] or 0

        past_paid = Payment.objects.filter(
            user=user, session__in=closed_sessions
        ).aggregate(total=Sum("total_paid"))["total"] or 0

        past_expected = (past_sessions_count * weekly_amount) + past_fines
        previous_due = max(0, past_expected - past_paid)

        # --- Total due this session ---
        amount_due = weekly_amount + fine_amount + previous_due
        paid = current_amount_paid >= amount_due

        # --- Attendance stats (all time) ---
        present_count = Record.objects.filter(user=user, status="present").count()
        late_count = Record.objects.filter(user=user, status="late").count()
        absent_count = Record.objects.filter(user=user, status="absent").count()

        # --- Total ever contributed ---
        total_paid_ever = Payment.objects.filter(user=user).aggregate(
            total=Sum("total_paid")
        )["total"] or 0

        # --- All transactions ---
        transactions = Transaction.objects.filter(
            user=user
        ).select_related("session").order_by("-created_at")

        # Accumulate group totals
        total_expected += amount_due
        total_collected += current_amount_paid
        total_fines += fine_amount
        total_pending += max(0, amount_due - current_amount_paid)

        members.append({
            "id": user.id,
            "name": user.name,
            "phone": getattr(user, "phone", ""),
            "role": user.role,

            "status": attendance_status,

            "weekly_amount": weekly_amount,
            "fine_amount": fine_amount,
            "previous_due": previous_due,

            "amount_due": amount_due,
            "amount_paid": current_amount_paid,
            "paid": paid,

            # Attendance stats
            "session_count": present_count,
            "late_payment_count": late_count,
            "absent_count": absent_count,

            # All-time totals
            "total_paid": total_paid_ever,

            "transactions": transactions,
        })

    # Global transactions for the ledger tab
    global_transactions = Transaction.objects.select_related(
        "user", "session"
    ).order_by("-created_at")

    collection_progress = 0
    if total_expected > 0:
        collection_progress = min(100, round((total_collected / total_expected) * 100))

    context = {
        "group": group,
        "active_session": active_session,
        "members": members,
        "total_members": len(members),
        "expected_collection": total_expected,
        "collected_amount": total_collected,
        "pending_amount": total_pending,
        "total_fine": total_fines,
        "collection_progress": collection_progress,
        "global_transactions": global_transactions,
    }

    return render(request, "payments/payment_ledger.html", context)


# =========================================
# SAVE AND CLOSE SESSION (payments app)
# =========================================

@login_required
def save_and_close_session(request):

    if request.method != "POST":
        return redirect("payment_ledger")

    if request.user.role != "admin" and not request.user.is_staff:
        messages.error(request, "Unauthorized.")
        return redirect("payment_ledger")

    group = Group.objects.first()
    active_session = Session.objects.filter(
        group=group, status="open"
    ).first()

    if not active_session:
        messages.error(request, "No active session found.")
        return redirect("payment_ledger")

    # Include ALL active users — admins and members both participate
    users = User.objects.filter(is_active=True)
    total_collected = 0

    for user in users:
        status = request.POST.get(f"status_{user.id}", "present")

        try:
            amount_paid = float(request.POST.get(f"amount_{user.id}", 0) or 0)
        except ValueError:
            amount_paid = 0

        # Calculate fine
        fine = 0
        if status == "late":
            fine = group.late_fine
        elif status == "absent":
            fine = group.absent_fine

        # Update or create attendance record
        record, _ = Record.objects.get_or_create(
            user=user, session=active_session
        )
        record.status = status
        record.fine = fine
        record.save()

        # Save payment (model's save() auto-calculates total_paid)
        if amount_paid > 0 or fine > 0:
            payment, _ = Payment.objects.get_or_create(
                user=user,
                session=active_session,
                defaults={"amount": 0, "fine_paid": 0},
            )
            payment.amount = amount_paid
            payment.fine_paid = fine
            payment.save()  # triggers total_paid = amount + fine_paid
            total_collected += payment.total_paid

        # Create investment transaction
        if amount_paid > 0:
            # Avoid duplicate transactions for the same session
            Transaction.objects.get_or_create(
                user=user,
                session=active_session,
                type="investment",
                defaults={"amount": amount_paid},
            )

        # Create fine transaction
        if fine > 0:
            Transaction.objects.get_or_create(
                user=user,
                session=active_session,
                type="fine",
                defaults={"amount": fine},
            )

    # Close the session
    active_session.status = "closed"
    active_session.end_datetime = timezone.now()
    active_session.save()

    messages.success(
        request,
        f"Session closed! Total collected: ₹{total_collected:.0f}"
    )
    return redirect("dashboard")
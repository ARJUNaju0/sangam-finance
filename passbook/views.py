from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from sangam.models import Transaction


@login_required
def passbook(request):
    user = request.user

    transactions = Transaction.objects.filter(user=user).order_by('-created_at')

    total_investment = sum(t.amount for t in transactions if t.type == 'investment')
    total_fine = sum(t.amount for t in transactions if t.type == 'fine')

    balance = total_investment - total_fine

    return render(request, 'passbook/passbook.html', {
        'transactions': transactions,
        'total_investment': total_investment,
        'total_fine': total_fine,
        'balance': balance
    })


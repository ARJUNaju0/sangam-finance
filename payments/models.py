from django.db import models
from django.utils import timezone
from accounts.models import User
from sangam.models import Session


class Payment(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)

    amount = models.FloatField(default=0)
    fine_paid = models.FloatField(default=0)

    total_paid = models.FloatField(default=0)

    paid_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['user', 'session']

    def save(self, *args, **kwargs):
        self.total_paid = (self.amount or 0) + (self.fine_paid or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - ₹{self.total_paid}"





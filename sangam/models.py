from django.db import models
from django.utils import timezone
from django.conf import settings


# =========================================================
# GROUP / SANGAM
# =========================================================

class Group(models.Model):

    name = models.CharField(max_length=100)

    meeting_day = models.CharField(max_length=20)

    start_time = models.IntegerField()

    end_time = models.IntegerField()

    weekly_amount = models.FloatField()

    late_fine = models.FloatField()

    absent_fine = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# =========================================================
# WEEKLY SESSION
# =========================================================

class Session(models.Model):

    STATUS_CHOICES = (
        ("open", "Open"),
        ("closed", "Closed"),
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE
    )

    date = models.DateField()

    start_datetime = models.DateTimeField(
        null=True,
        blank=True
    )

    end_datetime = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="open"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.group.name} - {self.date}"


# =========================================================
# ATTENDANCE RECORD
# =========================================================

class Record(models.Model):

    STATUS_CHOICES = (
        ("present", "Present"),
        ("late", "Late"),
        ("absent", "Absent"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="absent"
    )

    fine = models.FloatField(default=0)

    absence_count = models.IntegerField(default=0)

    marked_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "session")

    def __str__(self):
        return f"{self.user} - {self.session} - {self.status}"


# =========================================================
# PAYMENT
# =========================================================

class Payment(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE
    )

    amount = models.FloatField()

    fine_paid = models.FloatField(default=0)

    total_paid = models.FloatField(default=0)

    paid_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "session")

    def save(self, *args, **kwargs):

        self.total_paid = self.amount + self.fine_paid

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.total_paid}"


# =========================================================
# TRANSACTION LEDGER
# =========================================================

class Transaction(models.Model):

    TRANSACTION_TYPE = (
        ("investment", "Investment"),
        ("fine", "Fine"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE
    )

    amount = models.FloatField()

    type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.amount} ({self.type})"


# =========================================================
# GROUP SETTINGS
# =========================================================

class SangamSettings(models.Model):

    group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE
    )

    weekly_amount = models.FloatField()

    late_fine = models.FloatField()

    absent_base_fine = models.FloatField()

    def __str__(self):
        return f"Settings - {self.group.name}"
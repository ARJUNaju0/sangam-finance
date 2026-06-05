from django.db import models
from django.utils import timezone
from django.conf import settings
from accounts.models import User

# =========================================================
# GROUP / SANGAM
# =========================================================

class Group(models.Model):

    WEEK_DAYS = [
        ('Sunday', 'Sunday'),
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    ]

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True, null=True)

    meeting_day = models.CharField(
        max_length=20,
        choices=WEEK_DAYS,
        default='Sunday'
    )

    start_time = models.TimeField()

    end_time = models.TimeField(blank=True, null=True)

    weekly_amount = models.FloatField(default=0)

    increment_amount = models.FloatField(default=0)

    late_fine = models.FloatField(default=0)

    absent_fine = models.FloatField(default=0)

    max_members = models.IntegerField(default=50)

    reminder_enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

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




class ActivityLog(models.Model):

    ACTIONS = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('payment', 'Payment'),
        ('attendance', 'Attendance'),
        ('session', 'Session'),
        ('fine', 'Fine'),
        ('group', 'Group'),
        ('member', 'Member'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action_type = models.CharField(max_length=30, choices=ACTIONS)

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message
from sangam.models import ActivityLog


def log_activity(user, action_type, message):

    ActivityLog.objects.create(
        user=user,
        action_type=action_type,
        message=message
    )
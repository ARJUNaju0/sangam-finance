from sangam.models import Record

def calculate_fine(user, group, session):
    last_record = (
        Record.objects
        .filter(user=user, session__date__lt=session.date)
        .order_by('-session__date')
        .first()
    )

    if last_record and last_record.status == 'absent':
        count = getattr(last_record, 'absence_count', 0) + 1
    else:
        count = 1

    fine = group.late_fine * count

    return fine, count
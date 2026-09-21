from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Attempt


def send_mailing(mailing):
    """Отправляет письма всем получателям рассылки. Возвращает кортеж (успешно, всего).
    Создаёт записи Attempt через bulk_create."""
    if not (mailing.start_time <= timezone.now() <= mailing.end_time):
        raise ValueError("Рассылка неактивна в текущее время")

    recipients = mailing.recipients.all()
    message = mailing.message
    attempts = []

    for client in recipients:
        try:
            send_mail(
                subject=message.title,
                message=message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[client.email],
                fail_silently=False,
            )
            status = "success"
            server_response = "Письмо отправлено"
        except Exception as e:
            status = "failure"
            server_response = str(e)

        attempts.append(
            Attempt(
                mailing=mailing,
                status=status,
                server_response=server_response,
            )
        )

    # batch-создание
    Attempt.objects.bulk_create(attempts)
    success_count = sum(1 for a in attempts if a.status == "success")
    return success_count, len(attempts)

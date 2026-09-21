from django.core.management.base import BaseCommand
from django.utils import timezone

from mailings.models import Mailing
from mailings.services import send_mailing


class Command(BaseCommand):
    help = "Запускает все активные рассылки (по расписанию или вручную)"

    def handle(self, *args, **options):
        now = timezone.now()
        mailings = Mailing.objects.filter(start_time__lte=now, end_time__gte=now)
        if not mailings:
            self.stdout.write("Нет активных рассылок на текущий момент.")
            return

        for mailing in mailings:
            self.stdout.write(f"Обработка рассылки #{mailing.pk}...")
            try:
                sent, total = send_mailing(mailing)
                self.stdout.write(self.style.SUCCESS(f"  Отправлено {sent} из {total}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Ошибка: {e}"))

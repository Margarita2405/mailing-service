from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Client(models.Model):
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=150, verbose_name="Ф.И.О.")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Владелец"
    )

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылок"
        ordering = ["email"]

    def __str__(self):
        return self.email


class Message(models.Model):
    title = models.CharField(max_length=255, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Тело письма")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Владелец"
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["title"]

    def __str__(self):
        return self.title


class Mailing(models.Model):
    STATUS_CHOICES = [
        ("created", "Создана"),
        ("started", "Запущена"),
        ("completed", "Завершена"),
    ]
    start_time = models.DateTimeField(verbose_name="Время начала")
    end_time = models.DateTimeField(verbose_name="Время окончания")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created", verbose_name="Статус")
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="mailings", verbose_name="Сообщение")
    recipients = models.ManyToManyField(Client, related_name="mailings", verbose_name="Получатели")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Владелец"
    )

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        permissions = [
            ("can_view_all_mailings", "Может просматривать все рассылки"),
            ("can_view_all_clients", "Может просматривать всех клиентов"),
            ("can_view_users", "Может просматривать список пользователей"),
            ("can_block_users", "Может блокировать пользователей"),
            ("can_disable_mailings", "Может отключать рассылки"),
        ]

    def __str__(self):
        return f"Рассылка #{self.pk} - ({self.get_status_display()})"

    def update_status(self):
        """Обновляет статус рассылки на основе текущего времени и сохраняет в БД."""
        now = timezone.now()
        if now < self.start_time:
            new_status = "created"
        elif self.start_time <= now <= self.end_time:
            new_status = "started"
        else:
            new_status = "completed"

        if self.status != new_status:
            self.status = new_status

    def clean(self):
        """Валидация на уровне модели (вызывается при вызове full_clean())."""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Время начала должно быть раньше времени окончания.")
        # if self.start_time and self.start_time < timezone.now():
        # raise ValidationError("Время начала не может быть в прошлом.")

    def save(self, *args, **kwargs):
        # Вызываем валидацию перед сохранением (если не вызывается явно)
        self.full_clean()
        # Обновляем статус, если нужно (например, при создании или изменении времени)
        if self.pk is None:
            # Новая запись – вычислим статус при первом сохранении
            self.update_status()
        super().save(*args, **kwargs)


class Attempt(models.Model):
    STATUS_CHOICES = [
        ("success", "Успешно"),
        ("failure", "Не успешно"),
    ]
    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время попытки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Статус")
    server_response = models.TextField(verbose_name="Ответ почтового сервера")
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name="attempts", verbose_name="Рассылка")

    class Meta:
        verbose_name = "Попытка рассылок"
        verbose_name_plural = "Попытки рассылок"
        ordering = ["-attempt_time"]

    def __str__(self):
        return f"Попытка #{self.pk} – {self.get_status_display()}"

from django.contrib import admin

from .models import Attempt, Client, Mailing, Message


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "owner")
    list_filter = ("owner",)
    search_fields = ("email", "full_name")
    raw_id_fields = ("owner",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("title", "owner")
    list_filter = ("owner",)
    search_fields = ("title",)


class AttemptInline(admin.TabularInline):
    model = Attempt
    extra = 0
    fields = ("attempt_time", "status", "server_response")
    readonly_fields = ("attempt_time",)
    can_delete = False
    show_change_link = True


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "status", "start_time", "end_time", "owner")
    list_filter = ("status", "owner", "start_time")
    search_fields = ("message__title",)
    raw_id_fields = ("message", "owner")
    filter_horizontal = ("recipients",)
    readonly_fields = ("status",)
    inlines = [AttemptInline]
    fieldsets = (
        (None, {"fields": ("message", "recipients", "start_time", "end_time", "owner")}),
        ("Статус", {"fields": ("status",), "classes": ("collapse",)}),
    )

    def save_model(self, request, obj, form, change):
        # При сохранении через админку вызываем обновление статуса
        obj.save()
        obj.update_status()


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("attempt_time", "mailing", "status", "server_response")
    list_filter = ("status", "attempt_time")
    search_fields = ("mailing__message__title", "server_response")
    raw_id_fields = ("mailing",)
    readonly_fields = ("attempt_time", "mailing", "status", "server_response")
    can_delete = True

    def has_add_permission(self, request):
        # Запрещаем создание попыток вручную через админку
        return False

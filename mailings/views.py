from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import ClientForm, MailingForm, MessageForm
from .models import Attempt, Client, Mailing, Message
from .services import send_mailing


class HomeView(TemplateView):
    template_name = "mailings/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        # Кешируем общую статистику на 15 минут
        cache_key = "home_stats"
        stats = cache.get(cache_key)
        if not stats:
            total_mailings = Mailing.objects.count()
            active_mailings = Mailing.objects.filter(start_time__lte=now, end_time__gte=now).count()
            unique_clients = Client.objects.count()
            stats = {
                "total_mailings": total_mailings,
                "active_mailings": active_mailings,
                "unique_clients": unique_clients,
            }
            cache.set(cache_key, stats, 60 * 15)
        context.update(stats)

        # Персональная статистика для авторизованного пользователя
        if self.request.user.is_authenticated:
            user_mailings = Mailing.objects.filter(owner=self.request.user)
            attempts = Attempt.objects.filter(mailing__in=user_mailings)
            total_attempts = attempts.count()
            success_attempts = attempts.filter(status="success").count()
            failed_attempts = total_attempts - success_attempts
            context["total_attempts"] = total_attempts
            context["success_attempts"] = success_attempts
            context["failed_attempts"] = failed_attempts
            context["sent_messages"] = success_attempts  # по заданию – количество отправленных сообщений

            # Последние 5 попыток (только для рассылок пользователя)
            context["recent_attempts"] = attempts.select_related("mailing__message").order_by("-attempt_time")[:5]

        return context


# @method_decorator(cache_page(60 * 10), name='dispatch')  # кеш на 10 минут
# @method_decorator(vary_on_headers('Cookie'), name='dispatch')  # чтобы разные пользователи видели своё
class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = "mailings/client_list.html"
    context_object_name = "clients"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if user.has_perm("mailings.can_view_all_clients"):
            return Client.objects.all()
        return Client.objects.filter(owner=user)


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = "mailings/client_detail.html"
    context_object_name = "client"

    def get_queryset(self):
        user = self.request.user
        if user.has_perm("mailings.can_view_all_clients"):
            return Client.objects.all()
        return Client.objects.filter(owner=user)


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "mailings/client_form.html"
    success_url = reverse_lazy("mailings:client_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "mailings/client_form.html"
    success_url = reverse_lazy("mailings:client_list")

    def get_queryset(self):
        return Client.objects.filter(owner=self.request.user)


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = "mailings/client_confirm_delete.html"
    success_url = reverse_lazy("mailings:client_list")

    def get_queryset(self):
        return Client.objects.filter(owner=self.request.user)


# @method_decorator(cache_page(60 * 10), name='dispatch')
# @method_decorator(vary_on_headers('Cookie'), name='dispatch')
class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = "mailings/message_list.html"
    context_object_name = "messages"

    def get_queryset(self):
        user = self.request.user
        if user.has_perm("mailings.can_view_all_mailings"):
            return Message.objects.all()
        return Message.objects.filter(owner=user)


class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = "mailings/message_detail.html"
    context_object_name = "message"

    def get_queryset(self):
        user = self.request.user
        if user.has_perm("mailings.can_view_all_mailings"):
            return Message.objects.all()
        return Message.objects.filter(owner=user)


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailings/message_form.html"
    success_url = reverse_lazy("mailings:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailings/message_form.html"
    success_url = reverse_lazy("mailings:message_list")

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = "mailings/message_confirm_delete.html"
    success_url = reverse_lazy("mailings:message_list")

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)


# @method_decorator(cache_page(60 * 10), name='dispatch')
# @method_decorator(vary_on_headers('Cookie'), name='dispatch')
class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = "mailings/mailing_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        user = self.request.user
        qs = Mailing.objects.select_related("message").prefetch_related("recipients")
        if user.has_perm("mailings.can_view_all_mailings"):
            return qs
        return qs.filter(owner=user)


@method_decorator(cache_page(60 * 5), name="dispatch")
class MailingDetailView(LoginRequiredMixin, DetailView):
    model = Mailing
    template_name = "mailings/mailing_detail.html"
    context_object_name = "mailing"

    def get_queryset(self):
        user = self.request.user
        if user.has_perm("mailings.can_view_all_mailings"):
            return Mailing.objects.all()
        return Mailing.objects.filter(owner=user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()  # обновляем статус при просмотре
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()
        return context


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:mailing_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        self.object.update_status()  # установить статус после создания
        return response


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    success_url = reverse_lazy("mailings:mailing_list")

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.update_status()
        return response


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    model = Mailing
    template_name = "mailings/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailings:mailing_list")

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)


@login_required
@permission_required("mailings.can_disable_mailings", raise_exception=True)
def disable_mailing(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    if mailing.status != "completed":
        mailing.status = "completed"
        mailing.save()
        messages.success(request, f"Рассылка #{pk} отключена.")
    else:
        messages.warning(request, "Рассылка уже завершена.")
    return redirect("mailings:mailing_list")


# @method_decorator(cache_page(60 * 10), name='dispatch')
# @method_decorator(vary_on_headers('Cookie'), name='dispatch')
class AttemptListView(LoginRequiredMixin, ListView):
    model = Attempt
    template_name = "mailings/attempt_list.html"
    context_object_name = "attempts"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if user.has_perm("mailings.can_view_all_mailings"):
            return Attempt.objects.select_related("mailing", "mailing__message").all()
        user_mailings = Mailing.objects.filter(owner=user)
        return Attempt.objects.filter(mailing__in=user_mailings).select_related("mailing", "mailing__message")


# Ручной запуск рассылки
@login_required
def send_mailing_manually(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    # Проверка прав: владелец или менеджер
    if mailing.owner != request.user and not request.user.has_perm("mailings.can_view_all_mailings"):
        messages.error(request, "У вас нет прав для запуска этой рассылки")
        return redirect("mailings:mailing_list")

    now = timezone.now()
    if not (mailing.start_time <= now <= mailing.end_time):
        messages.error(request, "Рассылка не может быть запущена сейчас (время не входит в интервал)")
        return redirect("mailings:mailing_detail", pk=pk)

    try:
        sent, total = send_mailing(mailing)
        messages.success(request, f"Рассылка выполнена. Отправлено {sent} из {total} писем.")
    except ValueError as e:
        messages.error(request, str(e))

    return redirect("mailings:mailing_detail", pk=pk)

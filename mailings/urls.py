from django.urls import path

from mailings.apps import MailingsConfig

from . import views

app_name = MailingsConfig.name

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("clients/", views.ClientListView.as_view(), name="client_list"),
    path("clients/<int:pk>/", views.ClientDetailView.as_view(), name="client_detail"),
    path("clients/create/", views.ClientCreateView.as_view(), name="client_create"),
    path("clients/<int:pk>/update/", views.ClientUpdateView.as_view(), name="client_update"),
    path("clients/<int:pk>/delete/", views.ClientDeleteView.as_view(), name="client_delete"),
    path("messages/", views.MessageListView.as_view(), name="message_list"),
    path("messages/<int:pk>/", views.MessageDetailView.as_view(), name="message_detail"),
    path("messages/create/", views.MessageCreateView.as_view(), name="message_create"),
    path("messages/<int:pk>/update/", views.MessageUpdateView.as_view(), name="message_update"),
    path("messages/<int:pk>/delete/", views.MessageDeleteView.as_view(), name="message_delete"),
    path("mailings/", views.MailingListView.as_view(), name="mailing_list"),
    path("mailings/<int:pk>/", views.MailingDetailView.as_view(), name="mailing_detail"),
    path("mailings/create/", views.MailingCreateView.as_view(), name="mailing_create"),
    path("mailings/<int:pk>/update/", views.MailingUpdateView.as_view(), name="mailing_update"),
    path("mailings/<int:pk>/delete/", views.MailingDeleteView.as_view(), name="mailing_delete"),
    path("mailings/<int:pk>/send/", views.send_mailing_manually, name="send_mailing"),
    path("mailings/<int:pk>/disable/", views.disable_mailing, name="disable_mailing"),
    path("attempts/", views.AttemptListView.as_view(), name="attempt_list"),
]

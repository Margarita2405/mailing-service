from django import forms

from .models import Client, Mailing, Message


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["email", "full_name", "comment"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Введите email"}),
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Введите Ф.И.О."}),
            "comment": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Напишите комментарий", "rows": 3}
            ),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["title", "body"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Тема письма"}),
            "body": forms.Textarea(attrs={"class": "form-control", "placeholder": "Тело письма", "rows": 5}),
        }


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ["start_time", "end_time", "message", "recipients"]
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "message": forms.Select(attrs={"class": "form-control"}),
            "recipients": forms.SelectMultiple(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["message"].queryset = Message.objects.filter(owner=user)
            self.fields["recipients"].queryset = Client.objects.filter(owner=user)

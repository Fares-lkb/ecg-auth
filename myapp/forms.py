# forms.py

from django import forms
from .models import UserDB, ECGRecord


class UserWithECGForm(forms.ModelForm):
    ecg_file = forms.FileField(
        label="ECG File", required=False
    )  # Make it not required for editing

    class Meta:
        model = UserDB
        fields = ["first_name", "last_name", "matricule", "ecg_file"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If this is an edit (instance already exists), make ECG file not required
        if self.instance and self.instance.pk:
            self.fields["ecg_file"].widget = forms.HiddenInput()
            self.fields["ecg_file"].required = False

    def save(self, commit=True):
        # Save the user first with commit=True
        user = super().save(commit=True)  # ✅ commit=True is REQUIRED here

        # Only create ECG record if this is a new user (not editing)
        # and if an ECG file was provided
        if not self.instance.pk and self.cleaned_data.get("ecg_file"):
            ecg = ECGRecord(
                user=user,
                ecg_file=self.cleaned_data["ecg_file"],
                session_number=1,
                record_number=1,
            )
            ecg.save()

        return user


from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]


# ✅ Formulaire pour la réinitialisation du mot de passe admin
class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Adresse e-mail admin", max_length=254)
    role = forms.ChoiceField(
        label="Rôle utilisateur",
        choices=[
            ("staff", "Staff Admin"),
            ("superuser", "Super Admin"),
        ],
        widget=forms.RadioSelect,
        initial="staff",
        help_text="Sélectionnez le rôle pour cet utilisateur",
    )

from django.core.validators import FileExtensionValidator
from django import forms
from django.core.exceptions import ValidationError
# from .models import Note
from django.contrib.auth import get_user_model

from .models import Note

def validate_file_size(value):
    filesize = value.size
    if filesize > 20 * 1024 * 1024:  # 20MB
        raise ValidationError("The maximum file size that can be uploaded is 20MB")
    return value

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control'}),
        }

class UserLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class UserSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Confirm Password")

    class Meta:
        model = get_user_model()
        fields = ['full_name', 'email', 'password']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data

class QuizGenerationForm(forms.Form):
    content = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Paste your notes here...'}),
        required=False,
        help_text="Paste your notes or text here."
    )
    file = forms.FileField(
        required=False,
        help_text="Or upload a PDF file (.pdf).",
        validators=[FileExtensionValidator(allowed_extensions=['pdf']), validate_file_size]
    )
    num_questions = forms.IntegerField(
        label="Number of Questions",
        min_value=5,
        max_value=20,
        initial=5,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Specify how many questions to generate (min 5, max 20)."
    )

    def clean(self):
        cleaned_data = super().clean()
        content = cleaned_data.get('content')
        file = cleaned_data.get('file')

        if not content and not file:
            raise forms.ValidationError("Please provide either text content or upload a file.")
        if content and file:
            raise forms.ValidationError("Please provide either text content OR upload a file, not both.")

        return cleaned_data
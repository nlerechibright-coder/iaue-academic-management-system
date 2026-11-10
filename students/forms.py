# students/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import StudentProfile
from institution.models import Department, Programme

User = get_user_model()

class StudentCreationForm(forms.ModelForm):
    """
    Form for creating a new student. 
    Username and Matric Number are handled automatically.
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none',
            'placeholder': 'email@example.com'
        })
    )
    first_name = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none',
            'placeholder': 'Last Name'
        })
    )
    password = forms.CharField(
        label="Initial Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none',
            'autocomplete': 'new-password'
        }),
        help_text="Minimum 8 characters. Used for portal login."
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none',
            'autocomplete': 'new-password'
        })
    )
    
    # Academic Fields
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True,
        empty_label="-- Select Department --",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white'
        })
    )
    programme = forms.ModelChoiceField(
        queryset=Programme.objects.all(),
        required=False,
        empty_label="-- Select Programme --",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white'
        })
    )
    level = forms.IntegerField(
        min_value=100,
        max_value=600,
        initial=100,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
        })
    )
    qualification_type = forms.ChoiceField(
        choices=StudentProfile.QUALIFICATION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white'
        })
    )

    class Meta:
        model = StudentProfile
        # Exclude user, matric_number as they are managed programmatically
        exclude = ['user', 'matric_number', 'admission_year', 'created_at', 'updated_at']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
            
        return cleaned_data
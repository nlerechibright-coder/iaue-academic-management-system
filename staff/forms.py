# staff/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import StaffProfile
from institution.models import Department

User = get_user_model()

class StaffCreationForm(forms.ModelForm):
    """
    Combined form for creating a User and their associated StaffProfile.
    """
    # Fields from User model
    username = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-mono',
            'placeholder': 'e.g., jsmith'
        })
    )
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
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none',
            'autocomplete': 'new-password'
        }),
        help_text="Minimum 8 characters."
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none',
            'autocomplete': 'new-password'
        })
    )

    # Fields from StaffProfile model
    staff_id = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-mono',
            'placeholder': 'e.g., STAFF-001'
        })
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="-- Select Department --",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white'
        })
    )

    class Meta:
        model = StaffProfile
        fields = ['staff_id', 'department']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
            
        return cleaned_data

    def save(self, commit=True):
        # Create User first
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            is_staff=False, # Keep false unless they are also admin
            is_management=False
        )
        
        # Create Staff Profile linked to User
        profile = super().save(commit=False)
        profile.user = user
        
        if commit:
            profile.save()
            
        return profile
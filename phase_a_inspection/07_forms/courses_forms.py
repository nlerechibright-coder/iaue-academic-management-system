from django import forms
from .models import Course, CourseOffering, Section, LecturerAssignment
from staff.models import StaffProfile
from academics.models import AcademicSession

LEVEL_CHOICES = [(i*100, f'{i*100} Level') for i in range(1, 7)]

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'title', 'department', 'programme', 'level', 'semester', 'credit_units', 'is_compulsory', 'prerequisites']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'department': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'programme': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'level': forms.Select(choices=LEVEL_CHOICES, attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'semester': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'credit_units': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'prerequisites': forms.SelectMultiple(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
        }

class CourseOfferingForm(forms.ModelForm):
    # Custom text field for manual session input
    session_name = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none',
            'placeholder': 'e.g., 2023/2024'
        }),
        help_text="Type the session name. It will be created automatically if it doesn't exist."
    )

    class Meta:
        model = CourseOffering
        # Note: 'session' is intentionally excluded here so Django doesn't try to auto-map it
        fields = ['course', 'semester_type', 'level']
        widgets = {
            'course': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'semester_type': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'level': forms.Select(choices=LEVEL_CHOICES, attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
        }

    def clean_session_name(self):
        return self.cleaned_data['session_name'].strip()

    def save(self, commit=True):
        # Create the instance without saving to DB yet
        instance = super().save(commit=False)
        
        # Get or create the AcademicSession based on the typed name
        session_name = self.cleaned_data['session_name']
        session_obj, _ = AcademicSession.objects.get_or_create(name=session_name)
        
        # Assign the actual object to the ForeignKey
        instance.session = session_obj
        
        if commit:
            instance.save()
        return instance

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['offering', 'name', 'is_default']
        widgets = {
            'offering': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none', 'placeholder': 'e.g., A, B, Default'}),
        }

class LecturerAssignmentForm(forms.ModelForm):
    class Meta:
        model = LecturerAssignment
        fields = ['offering', 'section', 'lecturer']
        widgets = {
            'offering': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'section': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
            'lecturer': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'}),
        }

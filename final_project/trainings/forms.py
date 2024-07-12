from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone

from .models import Employee, Participant, TrainingCourse


class AddEmployeeForm(forms.ModelForm):
    phone_number = forms.CharField(
        validators=[RegexValidator(
            regex='^[0-9]{9}$',
            message='Numer telefonu musi składać się z 9 cyfr.')]
    )

    class Meta:
        model = Employee
        fields = ['first_name',
                  'last_name',
                  'gender',
                  'e_mail',
                  'phone_number',
                  'position',
                  'company',
                  'team',
                  'team_leader',
                  'supervisor'
                  ]


class EditEmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['phone_number',
                  'position',
                  'company',
                  'team',
                  'team_leader',
                  'supervisor'
                  ]


class AddParticipantForm(forms.ModelForm):
    training_course = forms.ModelMultipleChoiceField(
        queryset=TrainingCourse.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    phone_number = forms.CharField(
        validators=[RegexValidator(
            regex='^[0-9]{9}$',
            message='Numer telefonu musi składać się z 9 cyfr.')]
    )

    class Meta:
        model = Participant
        fields = ['first_name',
                  'last_name',
                  'gender',
                  'e_mail',
                  'phone_number',
                  'training_course']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.now()
        self.fields['training_course'].queryset = TrainingCourse.objects.filter(end_time__gt=today)

    def clean_training_course(self):
        selected_courses = self.cleaned_data.get('training_course')
        for course in selected_courses:
            if course.participant_set.count() >= course.participants_limit:
                raise ValidationError(f"Limit uczestników został osiągnięty dla szkolenia: "
                                      f"{course.topic} ({course.get_formula_display()})")
        return selected_courses


class AddCourseForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'})
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'})
    )

    class Meta:
        model = TrainingCourse
        fields = ['topic',
                  'start_time',
                  'end_time',
                  'category',
                  'path',
                  'formula',
                  'participants_limit',
                  'coach'
                  ]


class EditCourseFutureForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'}),
        error_messages={'invalid': 'Podaj poprawną datę i godzinę.'}
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'}),
        error_messages={'invalid': 'Podaj poprawną datę i godzinę.'}
    )

    participants_limit = forms.IntegerField(
        validators=[MinValueValidator(0,
                                      message="Liczba uczestników nie może być ujemna.")],
        error_messages={'invalid': 'Podaj poprawną liczbę uczestników.'}
    )

    class Meta:
        model = TrainingCourse
        fields = ['start_time',
                  'end_time',
                  'coach',
                  'participants_limit'
                  ]


class EditCoursePastForm(forms.ModelForm):
    class Meta:
        model = TrainingCourse
        fields = ['took_place',
                  'materials'
                  ]


class EditParticipantForm(forms.Form):
    participant = forms.ModelChoiceField(
        queryset=Participant.objects.all(),
        label='Uczestnik')
    training_course = forms.ModelChoiceField(
        queryset=TrainingCourse.objects.all(),
        label='Szkolenie')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.now()
        self.fields['training_course'].queryset = TrainingCourse.objects.filter(end_time__gt=today)

    def clean_training_course(self):
        selected_course = self.cleaned_data.get('training_course')
        if selected_course.participant_set.count() >= selected_course.participants_limit:
                raise ValidationError(f"Limit uczestników został osiągnięty dla szkolenia: "
                                      f"{selected_course.topic} ({selected_course.get_formula_display()})")
        return selected_course


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cd = super().clean()
        username = cd.get('username')
        password = cd.get('password')
        user = authenticate(username=username, password=password)
        if user is None:
            raise ValidationError("Podaj poprawny login lub hasło")
        else:
            self.user = user

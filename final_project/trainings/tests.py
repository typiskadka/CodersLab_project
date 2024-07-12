import pytest

from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.test import Client

from .forms import AddParticipantForm
from .models import Employee, TrainingCourse, Participant, PresenceList


@pytest.mark.django_db
def test_employees_view(authenticated_client, employee, training_course):
    url = reverse('employees_list')
    response = authenticated_client.get(url)

    assert response.status_code == 200
    assert 'employees_data' in response.context

    employees_data = response.context['employees_data']

    # Sprawdź, czy pracownik istnieje w `employees_data`
    employee_data = next((data for data in employees_data if data['employee'] == employee), None)
    assert employee_data is not None

    # Sprawdź, czy dane pracownika są poprawne
    assert employee_data['employee'].first_name == employee.first_name
    assert employee_data['employee'].last_name == employee.last_name
    assert employee_data['employee'].supervisor == employee.supervisor


@pytest.mark.django_db
def test_employees_view_delete(authenticated_client, employee):
    url = reverse('employees_list')
    data = {
        'delete': True,
        'employee_id': employee.id
    }
    response = authenticated_client.post(url, data)

    assert response.status_code == 302  # Check redirect
    assert not Employee.objects.filter(id=employee.id).exists()  # Employee should be deleted


@pytest.mark.django_db
def test_employees_view_generate_chart(authenticated_client, employee, training_course):
    url = reverse('employees_list')
    data = {
        'generate_chart': True
    }
    response = authenticated_client.post(url, data)

    assert response.status_code == 200
    assert 'chart' in response.context
    assert response.context['chart'] is not None


@pytest.mark.django_db
def test_add_employee_view(authenticated_client):
    url = reverse('add_employee')
    data = {
        'first_name': 'Jan',
        'last_name': 'Kowalski',
        'gender': 1,
        'e_mail': 'kowalski@example.com',
        'phone_number': 123456789,
        'position': 'Developer',
        'company': 'Company',
        'team': 'Good Team',
        'team_leader': 'Team Leader',
        'supervisor': 'Supervisor'
    }
    response = authenticated_client.post(url, data)

    assert response.status_code == 302  # Check for redirect after successful form submission
    assert Employee.objects.filter(first_name='Jan', last_name='Kowalski', position='Developer').exists()


@pytest.mark.django_db
def test_add_employee_view_validation_data(authenticated_client):
    url = reverse('add_employee')

    data = {
        'first_name': 'Jan',
        'last_name': 'Kowalski',
        'gender': 'M',
        'e_mail': 'kowalski@example.com',
        'phone_number': 123456789,
        'position': 'Developer',
        'company': 'Company',
        'team': 'Good Team',
        'team_leader': 'Team Leader',
        'supervisor': 'Supervisor'
    }

    response = authenticated_client.post(url, data)

    assert 'gender' in response.context['form'].errors
    assert Employee.objects.count() == 0


@pytest.mark.django_db
def test_edit_employee_view(authenticated_client, employee):
    url = reverse('edit_employee', kwargs={'pk': employee.pk})
    data = {
        'first_name': employee.first_name,
        'last_name': employee.last_name,
        'gender': employee.gender,
        'e_mail': employee.e_mail,
        'phone_number': 123456789,
        'position': 'Manager',
        'company': 'New Company',
        'team': 'Better Team',
        'team_leader': 'New Leader',
        'supervisor': 'New Supervisor'
    }
    response = authenticated_client.post(url, data)

    assert response.status_code == 302  # Check for redirect after successful form submission
    employee.refresh_from_db()  # Refresh the employee instance to get updated data
    assert employee.phone_number == 123456789
    assert employee.position == 'Manager'
    assert employee.company == 'New Company'
    assert employee.team == 'Better Team'
    assert employee.team_leader == 'New Leader'
    assert employee.supervisor == 'New Supervisor'


@pytest.mark.django_db
def test_add_participant_view(authenticated_client, training_course):
    url = reverse('add_participant')
    data = {
        'first_name': 'Anna',
        'last_name': 'Nowak',
        'gender': 1,
        'e_mail': 'anna.nowak@example.com',
        'phone_number': '123456789',
        'training_course': [training_course.id]
    }
    response = authenticated_client.post(url, data)

    assert response.status_code == 302  # Check for redirect after successful form submission
    assert Participant.objects.filter(first_name='Anna', last_name='Nowak').exists()


@pytest.mark.django_db
def test_add_participant_view_validation_data(authenticated_client):
    url = reverse('add_participant')
    data = {
        'first_name': '',
        'last_name': 'Nowak',
        'gender': 1,
        'e_mail': 'invalid-email',
        'phone_number': '123',
        'training_course': []
    }
    response = authenticated_client.post(url, data)

    assert response.status_code == 200  # Form re-rendered due to validation error
    assert 'form' in response.context
    assert response.context['form'].errors
    assert 'first_name' in response.context['form'].errors
    assert 'e_mail' in response.context['form'].errors
    assert 'phone_number' in response.context['form'].errors
    assert 'training_course' in response.context['form'].errors


@pytest.mark.django_db
def test_courses_view(authenticated_client, training_course):
    url = reverse('courses_list')
    response = authenticated_client.get(url)

    assert response.status_code == 200
    assert 'courses' in response.context
    assert training_course in response.context['courses']


@pytest.mark.django_db
def test_courses_view_generate_past_courses_pdf(authenticated_client, past_training_course):
    url = reverse('courses_list')
    response = authenticated_client.post(url, {'save_past_courses': True})

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response['Content-Disposition'] == 'attachment; filename=past_courses.pdf'


@pytest.mark.django_db
def test_courses_view_generate_course_pdf(authenticated_client, training_course):
    url = reverse('courses_list')
    response = authenticated_client.post(url, {'save_one_course': True, 'course_id': training_course.id})

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response['Content-Disposition'] == f'attachment; filename=course_{training_course.topic}.pdf'


@pytest.mark.django_db
def test_add_course_view(authenticated_client, employee):
    url = reverse('add_course')
    data = {
        'topic': 'Advanced Python',
        'start_time': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
        'end_time': (timezone.now() + timezone.timedelta(days=1, hours=2)).strftime('%Y-%m-%dT%H:%M'),
        'category': 1,
        'path': 1,
        'formula': 1,
        'participants_limit': 10,
        'coach': employee.id
    }
    response = authenticated_client.post(url, data)

    assert response.status_code == 302  # Check for redirection
    assert response.url == reverse('courses_list')  # Check the redirection URL
    assert TrainingCourse.objects.filter(topic='Advanced Python').exists()  # Check if the course was created


@pytest.mark.django_db
def test_add_course_view_validation_data(authenticated_client, employee):
    url = reverse('add_course')
    invalid_data = {
        'topic': '',  # Empty topic should trigger validation error
        'start_time': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
        'end_time': (timezone.now() + timezone.timedelta(days=1, hours=2)).strftime('%Y-%m-%dT%H:%M'),
        'category': 1,
        'path': 1,
        'formula': 1,
        'participants_limit': 10,
        'coach': employee.id
    }
    response = authenticated_client.post(url, invalid_data)

    assert response.status_code == 200  # Should not redirect
    assert 'form' in response.context
    assert response.context['form'].errors  # Check if there are form errors
    assert 'topic' in response.context['form'].errors  # Check if the topic field has an error


@pytest.mark.django_db
def test_course_details_view(authenticated_client, training_course):
    url = reverse('course_details', kwargs={'pk': training_course.pk})
    response = authenticated_client.get(url)

    assert response.status_code == 200
    assert 'course' in response.context
    assert 'form' in response.context
    assert response.context['course'] == training_course


@pytest.mark.django_db
def test_course_details_view_past_course(authenticated_client, training_course, employee):
    url = reverse('course_details', kwargs={'pk': training_course.pk})
    data = {
        'took_place': True,
        'materials': True,
        'save': 'save'
    }
    response = authenticated_client.post(url, data)

    assert response.status_code == 302  # Check for redirection
    assert response.url == reverse('course_details', kwargs={'pk': training_course.pk})  # Check the redirection URL

    # Fetch the updated course
    training_course.refresh_from_db()
    assert training_course.took_place == True
    assert training_course.materials == True


@pytest.mark.django_db
def test_employee_courses_view_generate_pdf(authenticated_client, employee, training_course):
    url = reverse('employee_courses', kwargs={'pk': employee.pk})
    data = {'save_to_pdf': 'save'}
    response = authenticated_client.post(url, data)

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert response['Content-Disposition'] == f'attachment; filename={employee.first_name}_{employee.last_name}_courses.pdf'


@pytest.mark.django_db
def test_courses_for_today_view(authenticated_client, training_course, past_training_course):
    url = reverse('courses_today')
    response = authenticated_client.get(url)

    assert response.status_code == 200
    assert 'courses_today' in response.context
    assert training_course in response.context['courses_today']
    assert past_training_course not in response.context['courses_today']


@pytest.mark.django_db
def test_courses_for_today_view_no_courses(authenticated_client, past_training_course):
    url = reverse('courses_today')
    response = authenticated_client.get(url)

    assert response.status_code == 200
    assert 'courses_today' in response.context
    assert past_training_course not in response.context['courses_today']
    assert not response.context['courses_today']  # Ensure courses_today is empty


@pytest.mark.django_db
def test_course_presence_list_view(authenticated_client, training_course, participant):
    url = reverse('course_presence_list', kwargs={'pk': training_course.pk})
    response = authenticated_client.get(url)

    assert response.status_code == 200
    assert 'course' in response.context
    assert 'participants' in response.context
    assert response.context['course'] == training_course
    assert participant in response.context['participants']


@pytest.mark.django_db
def test_course_presence_list_view_save_to_db(authenticated_client, training_course, participant):
    url = reverse('course_presence_list', kwargs={'pk': training_course.pk})
    post_data = {}
    for participant in training_course.participant_set.all():
        post_data[str(participant.id)] = 'on'

    response = authenticated_client.post(url, post_data)

    assert response.status_code == 302  # Check for redirection
    assert response.url == reverse('course_details', kwargs={'pk': training_course.pk})

    # Check if presence records were saved correctly
    for participant in training_course.participant_set.all():
        presence_record = PresenceList.objects.get(participant=participant, training_course=training_course)
        assert presence_record.present is True


@pytest.mark.django_db
def test_course_participants_view(authenticated_client, training_course, participant):
    url = reverse('course_participants', kwargs={'pk': training_course.pk})
    response = authenticated_client.get(url)

    assert response.status_code == 200
    assert 'course' in response.context
    assert 'participants' in response.context
    assert 'presence_list' in response.context

    assert response.context['course'].topic == 'Python Course'
    assert response.context['participants'].count() == 1
    assert response.context['participants'][0].first_name == 'Anna'
    assert response.context['presence_list'] is None


@pytest.mark.django_db
def test_course_participants_view_with_presence_list(authenticated_client, past_training_course_took_place, participant):
    # Simulate marking some participants as present
    PresenceList.objects.create(participant=participant, training_course=past_training_course_took_place, present=True)

    url = reverse('course_participants', kwargs={'pk': past_training_course_took_place.pk})
    response = authenticated_client.get(url)

    assert response.status_code == 200
    assert 'presence_list' in response.context

    presence_list = response.context['presence_list']
    assert presence_list.count() == 1
    assert presence_list[0].participant.first_name == 'Anna'
    assert presence_list[0].present is True


@pytest.mark.django_db
def test_edit_participant_view_successful(authenticated_client, training_course, participant_without_course):
    url = reverse('edit_participant')
    data = {
        'participant': participant_without_course.id,
        'training_course': training_course.id,
    }
    response = authenticated_client.post(url, data)
    assert response.status_code == 302  # Sprawdzamy przekierowanie
    participant_without_course.refresh_from_db()
    assert training_course in participant_without_course.training_course.all()


@pytest.mark.django_db
def test_edit_participant_view_already_registered(authenticated_client, training_course, participant):
    participant.training_course.add(training_course)  # Dodajemy uczestnika do szkolenia przed testem
    url = reverse('edit_participant')
    data = {
        'participant': participant.id,
        'training_course': training_course.id,
    }
    response = authenticated_client.post(url, data)
    assert response.status_code == 200  # Formularz powinien zostać ponownie wyrenderowany
    assert 'message' in response.context
    assert response.context['message'] == 'Uczestnik jest już zapisany na to szkolenie.'
    assert training_course in participant.training_course.all()


@pytest.mark.django_db
def test_edit_participant_view_post_limit_exceeded(authenticated_client, training_course, participant):
    # Ustawiamy limit uczestników na 1 dla testowego szkolenia
    training_course.participants_limit = 1
    training_course.save()

    # Dodajemy jednego uczestnika
    participant_2 = Participant.objects.create(
        first_name='Jan',
        last_name='Nowak',
        gender=1,
        e_mail='nowak@example.com',
        phone_number=987654321,
    )
    participant_2.training_course.add(training_course)

    # Próba dodania drugiego uczestnika, co powinno przekroczyć limit
    url = reverse('edit_participant')
    data = {
        'participant': participant.id,
        'training_course': training_course.id,
    }
    response = authenticated_client.post(url, data)

    assert response.status_code == 200  # Powinno zwrócić stronę z formularzem
    assert 'form' in response.context
    assert f'Limit uczestników został osiągnięty dla szkolenia: {training_course.topic} ({training_course.get_formula_display()})' in response.context['form'].errors['training_course']


@pytest.mark.django_db
def test_participants_list_view(authenticated_client, participant, training_course):
    # Upewnij się, że uczestnik ma przypisane szkolenie
    assert training_course in participant.training_course.all()

    # Wywołaj widok
    url = reverse('participants_list')
    response = authenticated_client.get(url)

    # Sprawdź, czy odpowiedź jest poprawna
    assert response.status_code == 200
    assert 'participants_courses' in response.context

    participants_courses = response.context['participants_courses']
    assert participant in participants_courses
    assert list(participants_courses[participant]) == list(participant.training_course.all())
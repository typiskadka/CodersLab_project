from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone
from django.urls import reverse

from trainings.models import Employee, TrainingCourse, Participant


@pytest.fixture
def user(db):
    # Użytkownik do testów
    return User.objects.create_user(username='testuser', password='testpassword')


@pytest.fixture
def client():
    # Klient Django do wysyłania żądań HTTP
    return Client()


@pytest.fixture
def authenticated_client(client, user):
    client.login(username='testuser', password='testpassword')
    return client

@pytest.fixture
def employee(db):
    return Employee.objects.create(
        first_name='Jan',
        last_name='Kowalski',
        gender=2,
        e_mail='kowalski@example.com',
        phone_number=123456789,
        position='Developer',
        company='Company',
        team='Good Team',
        team_leader='Team Leader',
        supervisor='Supervisor')

@pytest.fixture
def training_course(db, employee):
    return TrainingCourse.objects.create(
        topic='Python Course',
        start_time=timezone.now(),
        end_time=timezone.now() + timedelta(hours=2),
        category=1,
        path=1,
        formula=1,
        participants_limit=5,
        coach=employee,
        took_place=None,
        materials=None
    )

@pytest.fixture
def participant(db, training_course):
    participant = Participant.objects.create(
        first_name='Anna',
        last_name='Nowak',
        gender=1,
        e_mail='nowak@example.com',
        phone_number=987654321,
    )
    participant.training_course.add(training_course)  # Correct way to add to ManyToManyField
    return participant

@pytest.fixture
def participant_without_course(db):
    participant = Participant.objects.create(
        first_name='Anna',
        last_name='Nowak',
        gender=1,
        e_mail='nowak@example.com',
        phone_number=987654321,
    )
    return participant

@pytest.fixture
def past_training_course(db, employee):
    return TrainingCourse.objects.create(
        topic='Past Python Course',
        start_time=timezone.now() - timedelta(days=10),
        end_time=timezone.now() - timedelta(days=9, hours=22),
        category=1,
        path=1,
        formula=1,
        participants_limit=5,
        coach=employee,
        took_place=None,
        materials=True
    )

@pytest.fixture
def past_training_course_took_place(db, employee):
    return TrainingCourse.objects.create(
        topic='Past Python Course',
        start_time=timezone.now() - timedelta(days=10),
        end_time=timezone.now() - timedelta(days=9, hours=22),
        category=1,
        path=1,
        formula=1,
        participants_limit=5,
        coach=employee,
        took_place=True,
        materials=True
    )
import base64
import io
import matplotlib.pyplot as plt

from datetime import timedelta
from weasyprint import HTML

from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, View
from django.http import HttpResponse

from .models import (
    TrainingCourse,
    Employee,
    Participant,
    PresenceList
)
from .forms import (
    AddCourseForm,
    AddEmployeeForm,
    AddParticipantForm,
    EditCourseFutureForm,
    EditCoursePastForm,
    EditEmployeeForm,
    EditParticipantForm,
    LoginForm
)


class MainView(View):
    """
    Widok odpowiedzialny za renderowanie głównej strony aplikacji.

    Metody:
    - get(request): Obsługuje żądanie GET i renderuje szablon 'main.html'.
    """
    def get(self, request):
        """
        Obsługuje żądanie GET.

        :param:
            request (HttpRequest): Obiekt żądania HTTP.

        return:
            HttpResponse: Odpowiedź HTTP z wyrenderowanym szablonem 'main.html'.
        """
        return render(request, 'main.html')


class AuthenticatedView(LoginRequiredMixin, View):
    """
    Bazowa klasa widoku, która zapewnia, że tylko zalogowani użytkownicy mają dostęp do widoków dziedziczących po niej.

    Atrybuty:
    - login_url (str): URL strony logowania, na którą użytkownik zostanie przekierowany, jeśli nie jest zalogowany.
    - redirect_field_name (str): Nazwa parametru URL, który określa, gdzie przekierować użytkownika po zalogowaniu.
    """
    login_url = '/login/'
    redirect_field_name = 'redirect_to'


class EmployeesView(AuthenticatedView):
    """
    Widok do zarządzania danymi pracowników, dostępny tylko dla zalogowanych użytkowników.

    Metody:
    - get_employees_data: Pobiera dane pracowników wraz z łącznym czasem trwania szkoleń.
    - get: Wyświetla listę pracowników i opcjonalnie wykres.
    - post: Obsługuje usuwanie pracowników i generowanie wykresów.

    Dziedziczenie:
    Klasa dziedziczy po AuthenticatedView, co oznacza, że wymaga autoryzacji użytkownika przed dostępem.
    """
    def get_employees_data(self):
        """
        Pobiera dane wszystkich pracowników oraz łączny czas trwania szkoleń, do których są przypisani.

        return:
            employees_data: Lista słowników zawierających obiekty pracowników i ich łączny czas trwania szkoleń.
        """
        employees = Employee.objects.all()
        employees_data = []

        for employee in employees:
            total_duration = timedelta(seconds=0)
            courses = TrainingCourse.objects.filter(coach=employee)

            for course in courses:
                total_duration += course.duration

            employees_data.append({
                'employee': employee,
                'total_duration': total_duration,
            })
        return employees_data

    def get(self, request):
        """
        Obsługuje żądania GET, wyświetlając listę pracowników oraz opcjonalnie wykres.

        :param:
            request: Obiekt żądania HTTP.

        return:
            HttpResponse: Renderowana strona HTML z listą pracowników i opcjonalnie wykresem.
        """
        ctx = {
            'employees_data': self.get_employees_data(),
            'chart': None
        }
        return render(request, 'employees_list.html', ctx)

    def post(self, request):
        """
        Obsługuje żądania POST, umożliwiając usuwanie pracowników oraz generowanie wykresów.

        :param:
            request: Obiekt żądania HTTP.

        return:
            HttpResponse: Renderowana strona HTML z listą pracowników i opcjonalnie wykresem lub przekierowanie.
        """
        if 'delete' in request.POST:
            employee_id = request.POST.get('employee_id')
            employee = get_object_or_404(Employee, id=employee_id)

            # Sprawdź, czy pracownik jest przypisany do jakiegokolwiek szkolenia
            courses_exist = TrainingCourse.objects.filter(coach=employee).exists()

            if courses_exist:
                ctx = {
                    'employees_data': self.get_employees_data(),
                    'chart': None,
                    'error_message': f"Nie można usunąć pracownika {employee.first_name} {employee.last_name} - "
                                     f"jest przypisany do co najmniej jednego szkolenia."
                }
                return render(request, 'employees_list.html', ctx)
            else:
                employee.delete()
                return redirect('employees_list')

        elif 'generate_chart' in request.POST:
            employees_data = self.get_employees_data()
            employees_names = []
            total_durations = []

            for data in employees_data:
                employees_names.append(f"{data['employee'].first_name} {data['employee'].last_name}")
                total_durations.append(data['total_duration'].total_seconds() / 3600)

            plt.figure(figsize=(10, 6))
            plt.bar(employees_names, total_durations, color='blue')
            plt.xlabel('Pracownicy')
            plt.ylabel('Przepracowane godziny')
            plt.title('Czas trwania szkoleń według pracowników')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()

            # Convert PNG image to base64 string
            graph = base64.b64encode(image_png).decode('utf-8')

            ctx = {
                'employees_data': employees_data,
                'chart': graph
            }

            return render(request, 'employees_list.html', ctx)
        return redirect('employees_list')


class AddEmployeeView(AuthenticatedView):
    """
    Widok do dodawania nowych pracowników, dostępny tylko dla zalogowanych użytkowników.

    Metody:
    - get: Wyświetla formularz dodawania pracownika.
    - post: Obsługuje zapis nowego pracownika w bazie danych.

    Dziedziczenie:
    Klasa dziedziczy po AuthenticatedView, co oznacza, że wymaga autoryzacji użytkownika przed dostępem.
    """
    def get(self, request):
        """
        Obsługuje żądania GET, wyświetlając formularz dodawania pracownika.

        :param:
            request: Obiekt żądania HTTP.

        return:
            HttpResponse: Renderowana strona HTML z formularzem dodawania pracownika.
        """
        form = AddEmployeeForm()
        ctx = {
            'form': form
        }
        return render(request, 'add_employee.html', ctx)

    def post(self, request):
        """
        Obsługuje żądania POST, zapisując nowego pracownika w bazie danych, jeśli formularz jest poprawny.

        :param:
            request: Obiekt żądania HTTP.

        return:
            HttpResponse: Renderowana strona HTML z formularzem dodawania pracownika,
            jeśli formularz jest niepoprawny lub przekierowanie do listy pracowników po zapisaniu.
        """
        form = AddEmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employees_list')
        ctx = {
            'form': form
        }
        return render(request, 'add_employee.html', ctx)


class EditEmployeeView(AuthenticatedView):
    """
    Widok do edycji danych pracownika, dostępny tylko dla zalogowanych użytkowników.

    Metody:
    - get: Wyświetla formularz edycji danych pracownika.
    - post: Obsługuje zapis zmodyfikowanych danych pracownika w bazie danych.

    Dziedziczenie:
    Klasa dziedziczy po AuthenticatedView, co oznacza, że wymaga autoryzacji użytkownika przed dostępem.
    """
    def get(self, request, pk):
        """
        Obsługuje żądania GET, pobierając dane pracownika o podanym identyfikatorze
        i wyświetlając formularz edycji danych pracownika.

        :param:
            request: Obiekt żądania HTTP.
            pk: Identyfikator pracownika do edycji.

        return:
            HttpResponse: Renderowana strona HTML z formularzem edycji danych pracownika.
        """
        employee = get_object_or_404(Employee, pk=pk)
        form = EditEmployeeForm(instance=employee)
        ctx = {
            'form': form,
            'employee': employee
        }
        return render(request, 'edit_employee.html', ctx)

    def post(self, request, pk):
        """
        Obsługuje żądania POST, zapisując zmodyfikowane dane pracownika w bazie danych,
        jeśli formularz jest poprawny.

        :param:
            request: Obiekt żądania HTTP.
            pk: Identyfikator pracownika do edycji.

        Zwraca:
            HttpResponse: Przekierowanie do listy pracowników po zapisaniu zmian,
            lub renderowana strona HTML z formularzem edycji w przypadku błędów formularza.
        """
        employee = get_object_or_404(Employee, pk=pk)
        form = EditEmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('employees_list')
        ctx = {
            'form': form,
            'employee': employee
        }
        return render(request, 'edit_employee.html', ctx)


class AddParticipantView(AuthenticatedView):
    """
    Widok do dodawania nowego uczestnika, dostępny tylko dla zalogowanych użytkowników.

    Metody:
    - get: Wyświetla formularz dodawania uczestnika.
    - post: Obsługuje zapis danych nowego uczestnika do bazy danych.

    Dziedziczenie:
    Klasa dziedziczy po AuthenticatedView, co oznacza, że wymaga autoryzacji użytkownika przed dostępem.
    """
    def get(self, request):
        """
        Obsługuje żądania GET, tworząc formularz AddParticipantForm i renderując stronę HTML add_participant.html.

        :param:
            request: Obiekt żądania HTTP.

        return:
            HttpResponse: Renderowana strona HTML z formularzem dodawania uczestnika.
        """
        form = AddParticipantForm()
        ctx = {
            'form': form
        }
        return render(request, 'add_participant.html', ctx)

    def post(self, request):
        """
        Obsługuje żądania POST, zapisując dane nowego uczestnika do bazy danych, jeśli formularz jest poprawny.
        W przypadku niepoprawnego formularza, ponownie renderuje formularz wraz z błędami.

        :param:
            request: Obiekt żądania HTTP.

        return:
            HttpResponse: Przekierowanie do widoku 'main' po zapisaniu nowego uczestnika lub renderowana strona HTML z formularzem
                          dodawania uczestnika w przypadku błędów formularza.
        """
        form = AddParticipantForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main')
        ctx = {
            'form': form
        }
        return render(request, 'add_participant.html', ctx)


class CoursesView(AuthenticatedView):
    """
    Widok do zarządzania szkoleniami, dostępny tylko dla zalogowanych użytkowników.

    Metody:
    - generate_course_pdf(course_id): Generuje plik PDF dla konkretnego szkolenia na podstawie jego ID.
    - get: Wyświetla listę szkoleń posortowanych po czasie rozpoczęcia.
    - post: Obsługuje żądania POST, generując pliki PDF dla przeszłych szkoleń lub konkretnego szkolenia.

    Dziedziczenie:
    Klasa dziedziczy po AuthenticatedView, co oznacza, że wymaga autoryzacji użytkownika przed dostępem.
    """
    @staticmethod
    def generate_course_pdf(course_id):
        """
        Generuje plik PDF dla konkretnego szkolenia na podstawie jego ID.

        :param:
            course_id (int): ID szkolenia, dla którego generowany jest plik PDF.

        return:
            HttpResponse: Odpowiedź HTTP zawierająca plik PDF z danymi szkolenia.
        """
        # Pobierz szkolenie na podstawie ID
        course = get_object_or_404(TrainingCourse, pk=course_id)
        participants = Participant.objects.filter(training_course=course)

        # Sprawdź, czy szkolenie już się odbyło
        if course.took_place:
            presence_list = PresenceList.objects.filter(training_course=course).select_related('participant')
        else:
            presence_list = None

        # Kontekst dla szablonu PDF
        ctx = {
            'course': course,
            'participants': participants,
            'presence_list': presence_list,
        }

        # Generowanie PDF
        html_string = render_to_string('pdf/course_pdf.html', ctx)
        html = HTML(string=html_string)
        result = html.write_pdf()

        # Utwórz odpowiedź z plikiem PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=course_{course.topic}.pdf'
        response.write(result)
        return response

    @staticmethod
    def generate_past_courses_pdf():
        """
        Generuje plik PDF zawierający listę przeszłych szkoleń.

        return:
            HttpResponse: Odpowiedź HTTP zawierająca plik PDF z listą przeszłych szkoleń.
        """
        today = timezone.now().date()
        past_courses = TrainingCourse.objects.filter(end_time__date__lte=today)
        html_string = render_to_string('pdf/courses_past_pdf.html', {'courses': past_courses})
        html = HTML(string=html_string)
        result = html.write_pdf()

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=past_courses.pdf'
        response.write(result)
        return response

    def get(self, request):
        """
        Wyświetla listę szkoleń posortowanych po czasie rozpoczęcia.

        :param:
            request: Obiekt żądania HTTP.

        return:
            HttpResponse: Renderowana strona HTML z listą szkoleń.
        """
        courses = TrainingCourse.objects.all().order_by('start_time')
        ctx = {
            'courses': courses
        }
        return render(request, 'courses_list.html', ctx)

    def post(self, request):
        """
        Obsługuje żądania POST, generując pliki PDF dla przeszłych szkoleń lub konkretnego szkolenia.

        :param:
            request: Obiekt żądania HTTP.

        return:
            HttpResponse: Odpowiedź HTTP zawierająca wygenerowany plik PDF.
        """
        if 'save_past_courses' in request.POST:
            response = self.generate_past_courses_pdf()
            return response

        elif 'save_one_course' in request.POST:
            course_id = request.POST.get('course_id')
            response = self.generate_course_pdf(course_id)
            return response


class AddCourseView(AuthenticatedView):
    """
    Widok do dodawania nowego szkolenia.

    Metody:
    - get: Renderuje formularz dodawania nowego szkolenia.
    - post: Obsługuje żądania POST, zapisuje nowe szkolenie do bazy danych.

    Dziedziczenie:
    Klasa dziedziczy po AuthenticatedView, co oznacza, że wymaga autoryzacji użytkownika przed dostępem.
    """
    def get(self, request):
        """
        Renderuje formularz dodawania nowego szkolenia.

        :param:
            request: Obiekt żądania HTTP.

        return:
            HttpResponse: Renderowany formularz HTML do dodawania nowego szkolenia.
        """
        form = AddCourseForm()
        ctx = {
            'form': form
        }
        return render(request, 'add_course.html', ctx)

    def post(self, request):
        """
        Obsługuje żądania POST, zapisuje nowe szkolenie do bazy danych.

        :param:
            request: Obiekt żądania HTTP zawierający dane formularza.

        return:
            HttpResponseRedirect: Przekierowanie do widoku listy szkoleń po pomyślnym zapisie.
            HttpResponse: Renderowany formularz HTML z błędami walidacji, jeśli dane formularza są niepoprawne.
        """
        form = AddCourseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('courses_list')  # Przekierowanie do widoku listy szkoleń
        ctx = {
            'form': form
        }
        return render(request, 'add_course.html', ctx)


class CourseDetailsView(AuthenticatedView):
    """
    Widok szczegółowych informacji o szkoleniu.

    Metody:
    - get: Renderuje szczegółowe informacje o szkoleniu oraz formularz edycji, odpowiednio dostosowany do statusu szkolenia.
    - post: Obsługuje żądania POST, zapisuje zmiany w szkoleniu lub generuje raport PDF dla szkolenia.

    Dziedziczenie:
    Klasa dziedziczy po AuthenticatedView, co oznacza, że wymaga autoryzacji użytkownika przed dostępem.
    """
    def get(self, request, pk):
        """
        Renderuje szczegółowe informacje o szkoleniu oraz formularz edycji.

        :param:
            request: Obiekt żądania HTTP.
            pk: Klucz główny (ID) szkolenia.

        return:
            HttpResponse: Renderowane szczegółowe informacje o szkoleniu wraz z formularzem edycji.
        """
        course = get_object_or_404(TrainingCourse, pk=pk)
        participants_count = course.participant_set.count()

        today = timezone.now().date()
        if course.start_time.date() > today:
            form = EditCourseFutureForm(instance=course)
        else:
            form = EditCoursePastForm(instance=course)

        ctx = {
            'course': course,
            'form': form,
            'participants_count': participants_count,
            'today': today
        }
        return render(request, 'course_details.html', ctx)

    def post(self, request, pk):
        """
        Obsługuje żądania POST, zapisuje zmiany w szkoleniu lub generuje raport PDF dla szkolenia.

        :param:
            request: Obiekt żądania HTTP zawierający dane formularza.
            pk: Klucz główny (ID) szkolenia.

        return:
            HttpResponseRedirect: Przekierowanie do widoku szczegółowych informacji o szkoleniu po pomyślnym zapisie zmian.
            HttpResponse: Renderowany formularz HTML z błędami walidacji, jeśli dane formularza są niepoprawne.
        """
        course = get_object_or_404(TrainingCourse, pk=pk)
        today = timezone.now().date()

        if course.start_time.date() > today:
            form = EditCourseFutureForm(request.POST, instance=course)
        else:
            form = EditCoursePastForm(request.POST, instance=course)

        if 'save' in request.POST:
            if form.is_valid():
                form.save()
                return redirect('course_details', pk=pk)

            participants_count = course.participant_set.count()
            ctx = {
                'course': course,
                'form': form,
                'participants_count': participants_count,
                'today': today
            }
            return render(request, 'course_details.html', ctx)

        elif 'save_to_pdf' in request.POST:
            course_id = request.POST.get('course_id')
            response = CoursesView.generate_course_pdf(course_id)
            return response


class EmployeeCoursesView(AuthenticatedView):
    """
    Widok szczegółowych informacji o szkoleniach przypisanych do pracownika.

    Metody:
    - get: Renderuje szczegółowe informacje o szkoleniach przypisanych do pracownika.
    - post: Obsługuje żądania POST, generuje raport PDF zawierający szczegóły szkoleń przypisanych do pracownika.

    Dziedziczenie:
    Klasa dziedziczy po AuthenticatedView, co oznacza, że wymaga autoryzacji użytkownika przed dostępem.
    """
    def get(self, request, pk):
        """
        Renderuje szczegółowe informacje o szkoleniach przypisanych do pracownika.

        :param:
            request: Obiekt żądania HTTP.
            pk: Klucz główny (ID) pracownika.

        return:
            HttpResponse: Renderowane szczegółowe informacje o szkoleniach przypisanych do pracownika.
        """
        employee = get_object_or_404(Employee, pk=pk)
        courses = TrainingCourse.objects.filter(coach=employee)
        total_duration = sum([course.duration for course in courses], timedelta())

        ctx = {
            'employee': employee,
            'courses': courses,
            'total_duration': total_duration
        }
        return render(request, 'employee_courses.html', ctx)

    def post(self, request, pk):
        """
        Obsługuje żądania POST, generuje raport PDF zawierający szczegóły szkoleń przypisanych do pracownika.

        :param:
            request: Obiekt żądania HTTP zawierający dane formularza.
            pk: Klucz główny (ID) pracownika.

        return:
            HttpResponse: Generowany raport PDF zawierający szczegóły szkoleń przypisanych do pracownika.
        """
        employee = get_object_or_404(Employee, pk=pk)
        courses = TrainingCourse.objects.filter(coach=employee)
        total_duration = sum([course.duration for course in courses], timedelta())

        # Generate PDF
        html_string = render_to_string('pdf/employee_courses_pdf.html',
                                       {'employee': employee, 'courses': courses, 'total_duration': total_duration})
        html = HTML(string=html_string)
        result = html.write_pdf()

        # Create a response with the PDF file
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={employee.first_name}_{employee.last_name}_courses.pdf'
        response.write(result)
        return response


class CoursesForTodayView(AuthenticatedView):
    """
    Widok listy szkoleń zaplanowanych na dzisiaj.

    Metody:
    - get: Renderuje listę szkoleń zaplanowanych na dzisiaj.

    Dziedziczenie:
    Klasa dziedziczy po AuthenticatedView, co oznacza, że wymaga autoryzacji użytkownika przed dostępem.
    """
    def get(self, request):
        """
        Renderuje listę szkoleń zaplanowanych na dzisiaj.

        :param:
            request: Obiekt żądania HTTP.

        return:
            HttpResponse: Renderowana lista szkoleń zaplanowanych na dzisiaj.
        """
        today = timezone.now().date()
        courses_today = TrainingCourse.objects.filter(start_time__date=today)

        ctx = {
            'courses_today': courses_today,
        }
        return render(request, 'courses_for_today.html', ctx)


class CoursePresenceListView(AuthenticatedView):
    """
    Widok listy obecności uczestników na szkoleniu.

    Metody:
    - get: Renderuje listę uczestników i ich obecność na danym szkoleniu.
    - post: Zapisuje zmiany w liście obecności uczestników na danym szkoleniu.

    Dziedziczenie:
    Klasa dziedziczy po AuthenticatedView, co oznacza, że wymaga autoryzacji użytkownika przed dostępem.
    """
    def get(self, request, pk):
        """
        Renderuje listę uczestników i ich obecność na danym szkoleniu.

        :param:
            request: Obiekt żądania HTTP.
            pk (int): ID szkolenia.

        return:
            HttpResponse: Renderowana lista uczestników i ich obecność na danym szkoleniu.
        """
        course = get_object_or_404(TrainingCourse, pk=pk)
        participants = course.participant_set.all()

        ctx = {
            'course': course,
            'participants': participants,
        }
        return render(request, 'course_presence_list.html', ctx)

    def post(self, request, pk):
        """
        Zapisuje zmiany w liście obecności uczestników na danym szkoleniu.

        :param:
            request: Obiekt żądania HTTP.
            pk (int): ID szkolenia.

        return:
            HttpResponseRedirect: Przekierowanie na stronę szczegółów szkolenia po zapisaniu obecności.
        """
        course = get_object_or_404(TrainingCourse, pk=pk)
        participants = course.participant_set.all()

        # Obsługa zapisu obecności
        for participant in participants:
            present = request.POST.get(str(participant.id)) == 'on'
            # Sprawdź, czy uczestnik jest już na liście obecności
            obj, created = PresenceList.objects.get_or_create(participant=participant, training_course=course)
            obj.present = present
            obj.save()

        # Po zapisaniu obecności przekieruj na stronę z listą obecności
        return redirect('course_details', pk=pk)


class CourseParticipantsView(AuthenticatedView):
    """
    Widok listy uczestników danego szkolenia.

    Metoda:
    - get: Renderuje listę uczestników szkolenia wraz z ich obecnością (jeśli szkolenie już się odbyło).

    Dziedziczenie:
    Klasa dziedziczy po AuthenticatedView, co oznacza, że wymaga autoryzacji użytkownika przed dostępem.
    """
    def get(self, request, pk):
        """
        Renderuje listę uczestników danego szkolenia.

        :param:
            request: Obiekt żądania HTTP.
            pk (int): ID szkolenia.

        return:
            HttpResponse: Renderowana lista uczestników danego szkolenia.
        """
        course = get_object_or_404(TrainingCourse, pk=pk)
        participants = course.participant_set.all()

        # Sprawdź, czy szkolenie już się odbyło
        if course.took_place:
            presence_list = PresenceList.objects.filter(training_course=course).select_related('participant')
        else:
            presence_list = None

        ctx = {
            'course': course,
            'participants': participants,
            'presence_list': presence_list,
        }
        return render(request, 'course_participants.html', ctx)


class EditParticipantView(AuthenticatedView):
    """
    Widok edycji uczestnika szkolenia.

    Metody:
    - get: Renderuje formularz edycji uczestnika.
    - post: Obsługuje zapis uczestnika na szkolenie i przekierowuje do szczegółów szkolenia po zapisie.

    Dziedziczenie:
    Klasa dziedziczy po AuthenticatedView, co oznacza, że wymaga autoryzacji użytkownika przed dostępem.
    """
    def get(self, request):
        """
        Renderuje formularz edycji uczestnika szkolenia.

        :param:
            request: Obiekt żądania HTTP.

        return:
            HttpResponse: Renderowany formularz edycji uczestnika.
        """
        form = EditParticipantForm()
        return render(request, 'edit_participant.html', {'form': form})

    def post(self, request):
        """
        Obsługuje zapis uczestnika na szkolenie i przekierowuje do szczegółów szkolenia po zapisie.

        :param:
            request: Obiekt żądania HTTP.

        return:
            HttpResponse: Przekierowanie do widoku szczegółów szkolenia lub renderowanie formularza z błędami.
        """
        form = EditParticipantForm(request.POST)
        if form.is_valid():
            participant = form.cleaned_data['participant']
            training_course = form.cleaned_data['training_course']

            # Sprawdzamy, czy uczestnik jest już zapisany na szkolenie
            if training_course in participant.training_course.all():
                message = 'Uczestnik jest już zapisany na to szkolenie.'
            else:
                # Dodajemy uczestnika do szkolenia
                participant.training_course.add(training_course)
                message = 'Uczestnik został dodany do szkolenia.'

                course_id = training_course.id
                return redirect('course_details', pk=course_id)

            return render(request, 'edit_participant.html', {'form': form, 'message': message})

        return render(request, 'edit_participant.html', {'form': form})


class ParticipantsView(AuthenticatedView):
    """
    Widok listy uczestników szkoleń.

    Metody:
    - get: Pobiera i renderuje listę uczestników wraz z przypisanymi szkoleniami.

    Dziedziczenie:
    Klasa dziedziczy po AuthenticatedView, co oznacza, że wymaga autoryzacji użytkownika przed dostępem.
    """
    def get(self, request):
        """
        Pobiera listę uczestników wraz z przypisanymi szkoleniami i renderuje widok.

        :param:
            request: Obiekt żądania HTTP.

        :return:
            HttpResponse: Renderowany widok listy uczestników z przypisanymi szkoleniami.
        """
        participants = Participant.objects.all()

        # Tworzymy słownik, gdzie kluczem jest uczestnik, a wartością lista szkoleń
        participants_courses = {}
        for participant in participants:
            courses = participant.training_course.all()
            participants_courses[participant] = courses

        return render(request, 'participants_list.html', {'participants_courses': participants_courses})


class LoginView(FormView):
    """
    Widok logowania użytkownika.

    Atrybuty klasy:
    - form_class (LoginForm): Klasa formularza używana do logowania użytkownika.
    - template_name (str): Nazwa szablonu HTML używanego do renderowania formularza logowania.
    - success_url (str): Adres URL, do którego użytkownik zostanie przekierowany po udanym logowaniu.

    Metody:
    - form_valid: Przechwytuje poprawne przesłanie formularza logowania, loguje użytkownika i przekierowuje na success_url.
    """
    form_class = LoginForm
    template_name = 'login.html'
    success_url = reverse_lazy('main')

    def form_valid(self, form):
        """
        Wywoływana, gdy formularz logowania jest poprawny.

        :param:
            form (LoginForm): Przesłany formularz logowania.

        :return:
            HttpResponseRedirect: Przekierowanie na success_url po poprawnym zalogowaniu.
        """
        login(self.request, form.user)
        return super().form_valid(form)


class LogoutView(View):
    """
    Widok wylogowywania użytkownika.

    Metody:
    - get: Obsługuje żądanie GET, wylogowuje użytkownika i przekierowuje na widok 'main'.
    """
    def get(self, request):
        """
        Obsługuje żądanie GET, wylogowuje użytkownika i przekierowuje na widok 'main'.

        :param:
            request: Obiekt żądania HTTP.

       :return:
            HttpResponseRedirect: Przekierowanie na widok 'main' po wylogowaniu użytkownika.
        """
        logout(request)
        return redirect('main')



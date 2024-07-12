from datetime import timedelta

from django.db import models


CATEGORIES = (
    (1, "szkolenie"),
    (2, "warsztat"),
    (3, "wystąpienie"),
    (4, "webinar")
)

PATHS = (
    (1, "efektywność osobista"),
    (2, "merytoryczna"),
    (3, "przywództwo"),
    (4, "sprzedażowa")
)

FORMULAS = (
    (1, "online"),
    (2, "stacjonarnie")
)

GENDERS = (
    (1, "kobieta"),
    (2, "mężczyzna")
)


class Human(models.Model):
    first_name = models.CharField(max_length=64, blank=False)   # imię
    last_name = models.CharField(max_length=64, blank=False)    # nazwisko
    gender = models.IntegerField(choices=GENDERS)               # płeć
    e_mail = models.EmailField(max_length=128, blank=False)     # e-mail
    phone_number = models.IntegerField()                        # numer telefonu

    @property
    def name(self):
        return "{} {}".format(self.first_name, self.last_name)

    def __str__(self):
        return self.name


class Employee(Human):
    position = models.CharField(max_length=256, blank=False)    # stanowisko
    company = models.CharField(max_length=128, blank=False)     # spółka
    team = models.CharField(max_length=128)                     # zespół
    team_leader = models.CharField(max_length=128)              # lider
    supervisor = models.CharField(max_length=128)               # przełożony


class TrainingCourse(models.Model):
    topic = models.CharField(max_length=512, blank=False)           # temat
    start_time = models.DateTimeField(blank=False)                  # data i godzina rozpoczęcia
    end_time = models.DateTimeField(blank=False)                    # data i godzina zakończenia
    category = models.IntegerField(choices=CATEGORIES)              # kategoria (typ) szkolenia
    path = models.IntegerField(choices=PATHS)                       # ścieżka szkolenia
    formula = models.IntegerField(choices=FORMULAS)                 # formuła szkolenia (zdalnie, stacjonarnie)
    participants_limit = models.IntegerField()                      # limit uczestników
    coach = models.ForeignKey(Employee, on_delete=models.CASCADE)   # trener
    # domyślnie — None, kiedy przyjdzie czas danego szkolenia, można zmienić na True/False
    took_place = models.BooleanField(null=True, default=None)                  # czy szkolenie się odbyło
    materials = models.BooleanField(null=True, default=None)                   # czy trener dostarczył materiały po szkoleniu

    @property
    def duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return timedelta(0)

    @property
    def course_topic(self):
        return "{} ({})".format(self.topic, self.get_formula_display())

    def __str__(self):
        return self.course_topic


class Participant(Human):
    training_course = models.ManyToManyField(TrainingCourse, null=True)        # szkolenie/szkolenia, w których uczestniczył


class PresenceList(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)          # uczestnik
    training_course = models.ForeignKey(TrainingCourse, on_delete=models.CASCADE)   # szkolenie
    present = models.BooleanField(null=True)                                        # czy był obecny?

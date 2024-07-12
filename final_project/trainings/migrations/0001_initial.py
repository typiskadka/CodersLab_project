# Generated by Django 5.0.6 on 2024-07-06 11:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Human',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=64)),
                ('last_name', models.CharField(max_length=64)),
                ('gender', models.IntegerField(choices=[(1, 'kobieta'), (2, 'mężczyzna')])),
                ('e_mail', models.EmailField(max_length=128)),
                ('phone_number', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('human_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='trainings.human')),
                ('position', models.CharField(max_length=256)),
                ('company', models.CharField(max_length=128)),
                ('team', models.CharField(max_length=128)),
                ('team_leader', models.CharField(max_length=128)),
                ('supervisor', models.CharField(max_length=128)),
            ],
            bases=('trainings.human',),
        ),
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('human_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='trainings.human')),
            ],
            bases=('trainings.human',),
        ),
        migrations.CreateModel(
            name='TrainingCourse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(max_length=512)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('category', models.IntegerField(choices=[(1, 'szkolenie'), (2, 'warsztat'), (3, 'wystąpienie'), (4, 'webinar')])),
                ('path', models.IntegerField(choices=[(1, 'efektywność osobista'), (2, 'merytoryczna'), (3, 'przywództwo'), (4, 'sprzedażowa')])),
                ('formula', models.IntegerField(choices=[(1, 'online'), (2, 'stacjonarnie')])),
                ('participants_limit', models.IntegerField()),
                ('took_place', models.BooleanField(default=None)),
                ('materials', models.BooleanField(default=None)),
                ('coach', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trainings.employee')),
            ],
        ),
        migrations.CreateModel(
            name='PresenceList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('present', models.BooleanField(null=True)),
                ('training_course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trainings.trainingcourse')),
                ('participant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trainings.participant')),
            ],
        ),
        migrations.AddField(
            model_name='participant',
            name='training_course',
            field=models.ManyToManyField(to='trainings.trainingcourse'),
        ),
    ]

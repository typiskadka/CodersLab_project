# Generated by Django 5.0.6 on 2024-07-10 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trainings', '0002_alter_trainingcourse_materials_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='training_course',
            field=models.ManyToManyField(null=True, to='trainings.trainingcourse'),
        ),
    ]

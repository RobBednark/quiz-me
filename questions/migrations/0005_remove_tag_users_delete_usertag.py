# Generated by Django 5.0.3 on 2024-06-25 06:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0004_querypreferences'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tag',
            name='users',
        ),
        migrations.DeleteModel(
            name='UserTag',
        ),
    ]

# Generated by Django 5.0.3 on 2024-06-01 20:49

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0003_delete_quiz'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='QueryPreferences',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_added', models.DateTimeField(auto_now_add=True)),
                ('datetime_updated', models.DateTimeField(auto_now=True)),
                ('name', models.TextField(default='', max_length=1000)),
                ('date_last_used', models.DateTimeField(default=None, null=True)),
                ('is_default', models.BooleanField(default=False)),
                ('include_unanswered_questions', models.BooleanField(default=True)),
                ('include_questions_with_answers', models.BooleanField(default=True)),
                ('include_questions_without_answers', models.BooleanField(default=True)),
                ('limit_to_date_show_next_before_now', models.BooleanField(default=False)),
                ('sort_by_nulls_first', models.BooleanField(default=False)),
                ('sort_by_lowest_answered_count_first', models.BooleanField(default=False)),
                ('sort_by_questions_with_answers_first', models.BooleanField(default=False)),
                ('sort_by_newest_answered_first', models.BooleanField(default=False)),
                ('sort_by_oldest_answered_first', models.BooleanField(default=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

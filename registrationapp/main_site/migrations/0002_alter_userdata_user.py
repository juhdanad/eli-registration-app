# Generated by Django 4.2.4 on 2023-08-16 10:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_site', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdata',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL),
        ),
    ]

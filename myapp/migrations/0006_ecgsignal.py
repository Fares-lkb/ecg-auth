# Generated by Django 5.1.7 on 2025-05-15 09:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_info_created_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='ECGSignal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ecg_file', models.FileField(upload_to='ecg_files/')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='myapp.userdb')),
            ],
        ),
    ]

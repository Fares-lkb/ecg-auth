import os
from django.db import models
from django.utils import timezone


class Info(models.Model):
    username = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    matricule = models.CharField(max_length=50)
    fileupload = models.FileField(upload_to='uploads/')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.username} - {self.name} - {self.matricule}"
    

class UserDB(models.Model):
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    matricule = models.CharField(max_length=50)

    class Meta:
        managed = False  # VERY IMPORTANT — don’t let Django manage the table
        db_table = 'users'  # Exact table name from your MySQL db
        verbose_name = "User"               # ✅ utilisé dans le bouton
        verbose_name_plural = "Users"  
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.matricule})"
    

class ECGRecord(models.Model):
    user = models.ForeignKey(UserDB, on_delete=models.CASCADE)
    ecg_file = models.FileField(upload_to='ecg_files/')
    session_number = models.IntegerField(default=1)
    record_number = models.IntegerField(default=1)

    def __str__(self):
        return f"ECG for {self.user} - Session {self.session_number} / Record {self.record_number}"

LOGS_BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"
    
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    must_change_password = models.BooleanField(default=True)

class SVMModels(models.Model):
    nom = models.CharField(max_length=50)
    fichier_svm = models.FileField(upload_to="svm/")

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date, datetime
import os

@receiver(post_save, sender=ContactMessage)
def save_contact_message_log(sender, instance, created, **kwargs):
    if created:
        log_date_folder = os.path.join('messages', date.today().isoformat(), 'contact_messages')
        os.makedirs(log_date_folder, exist_ok=True)

        timestamp = datetime.now().strftime('%H-%M-%S')
        filename = f"{instance.name.replace(' ', '_')}_{timestamp}.txt"
        path = os.path.join(log_date_folder, filename)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"Name: {instance.name}\n")
            f.write(f"Email: {instance.email}\n")
            f.write(f"Message:\n{instance.message}\n")

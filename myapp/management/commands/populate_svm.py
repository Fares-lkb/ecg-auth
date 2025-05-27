import os
from django.core.files import File
from django.core.management.base import BaseCommand
from myapp.models import SVMModels  # remplace myapp par le nom exact de ton app

class Command(BaseCommand):
    help = 'Importe automatiquement les fichiers .pkl dans la base SVMModels'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='Chemin vers le dossier contenant les fichiers .pkl')

    def handle(self, *args, **kwargs):
        path = kwargs['path']
        if not os.path.exists(path):
            self.stdout.write(self.style.ERROR(f"❌ Dossier introuvable : {path}"))
            return

        for filename in os.listdir(path):
            if filename.endswith('.pkl'):
                file_path = os.path.join(path, filename)
                with open(file_path, 'rb') as f:
                    obj = SVMModels(nom=filename)
                    obj.fichier_svm.save(filename, File(f), save=True)
                    self.stdout.write(self.style.SUCCESS(f"✅ Importé : {filename}"))

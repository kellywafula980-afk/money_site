from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models

class Command(BaseCommand):
    help = 'Clean invalid UTF-8 bytes from all text fields in all models'

    def handle(self, *args, **options):
        for model in apps.get_models():
            self.stdout.write(f"Processing {model.__name__}...")
            for obj in model.objects.all():
                updated = False
                for field in model._meta.get_fields():
                    if isinstance(field, (models.CharField, models.TextField)):
                        value = getattr(obj, field.name, None)
                        if value and isinstance(value, str):
                            try:
                                cleaned = value.encode('utf-8', errors='ignore').decode('utf-8')
                                if cleaned != value:
                                    setattr(obj, field.name, cleaned)
                                    updated = True
                            except Exception:
                                setattr(obj, field.name, '')
                                updated = True
                if updated:
                    obj.save()
                    self.stdout.write(f"  Cleaned {model.__name__} ID {obj.pk}")
        self.stdout.write(self.style.SUCCESS("All models cleaned."))

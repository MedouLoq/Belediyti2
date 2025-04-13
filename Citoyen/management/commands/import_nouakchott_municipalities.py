# Citoyen/management/commands/create_nkc_municipalities.py
from django.core.management.base import BaseCommand
from Citoyen.models import Municipality

NKC_MUNICIPALITIES = [
    "Tevragh-Zeina", "Ksar", "Teyarett", "Dar Naim", 
    "Toujounine", "Sebkha", "El Mina", "Arafat", "Riyadh"
]

class Command(BaseCommand):
    help = 'Creates Municipality records for Nouakchott moughataas by name (no boundaries needed).'

    def handle(self, *args, **options):
        self.stdout.write("Creating/Checking Nouakchott Municipality records...")
        created_count = 0
        existing_count = 0
        for name in NKC_MUNICIPALITIES:
            obj, created = Municipality.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created: {name}"))
                created_count += 1
            else:
                existing_count += 1
        
        self.stdout.write(f"Finished. Created: {created_count}, Already Existed: {existing_count}")
import random
from django.core.management.base import BaseCommand
from catalog.models import Category, Product

class Command(BaseCommand):
    help = 'Populates the database with categories and products'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to populate the database...'))

        # --- CATEGORÍAS ---
        animal_category, created = Category.objects.get_or_create(name='Proteína de Origen Animal')
        if created:
            self.stdout.write(self.style.SUCCESS(f'Category "{animal_category.name}" created.'))

        vegetal_category, created = Category.objects.get_or_create(name='Proteína de Origen Vegetal')
        if created:
            self.stdout.write(self.style.SUCCESS(f'Category "{vegetal_category.name}" created.'))

        # --- PRODUCTOS ---
        products_data = {
            animal_category: [
                'Huevos', 'Leche', 'Queso Fresco', 'Yogur Griego', 'Pechuga de Pollo', 'Pechuga de Pavo',
                'Carne de Conejo', 'Carne de Vaca Magra', 'Atún', 'Salmón', 'Sardinas', 'Langostinos'
            ],
            vegetal_category: [
                'Lentejas', 'Garbanzos', 'Soja Texturizada', 'Tofu', 'Edamame', 'Cacahuetes',
                'Almendras', 'Semillas de Calabaza', 'Avena', 'Quinoa', 'Seitán', 'Brócoli'
            ]
        }

        for category, product_names in products_data.items():
            for product_name in product_names:
                # Evitar duplicados
                if not Product.objects.filter(name=product_name).exists():
                    product = Product.objects.create(
                        name=product_name,
                        brand='Marca Genérica',
                        category=category,
                        price=random.randint(3000, 15000),
                        protein_grams=f"{random.randint(10, 35)}g",
                        # Dejamos la imagen por defecto
                        price_lider=random.randint(2800, 16000),
                        price_jumbo=random.randint(2900, 15500)
                    )
                    self.stdout.write(self.style.SUCCESS(f'Product "{product.name}" created.'))
                else:
                    self.stdout.write(self.style.WARNING(f'Product "{product_name}" already exists. Skipping.'))

        self.stdout.write(self.style.SUCCESS('Database population complete!'))

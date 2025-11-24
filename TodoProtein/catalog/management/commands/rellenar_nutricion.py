import random
from django.core.management.base import BaseCommand
from catalog.models import Producto

class Command(BaseCommand):
    help = 'Rellena automáticamente la información nutricional faltante con datos simulados coherentes.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando actualización de información nutricional...")
        
        # Buscar productos que no tengan información nutricional completa (asumimos 0 o None)
        productos_sin_info = Producto.objects.filter(calories__lte=0)
        
        count = 0
        for prod in productos_sin_info:
            cat_name = prod.categoria.name.lower()
            
            # Valores base simulados según categoría
            if 'proteína' in cat_name or 'protein' in cat_name or 'suplemento' in cat_name:
                # Alto en proteína, bajo en carbohidratos
                prod.protein_grams = random.randint(20, 30)
                prod.fat_grams = round(random.uniform(1.0, 3.5), 1)
                prod.carbs_grams = round(random.uniform(2.0, 5.0), 1)
                prod.calories = (prod.protein_grams * 4) + (prod.fat_grams * 9) + (prod.carbs_grams * 4)
                
            elif 'snack' in cat_name or 'barra' in cat_name:
                # Balanceado
                prod.protein_grams = random.randint(10, 20)
                prod.fat_grams = round(random.uniform(5.0, 12.0), 1)
                prod.carbs_grams = round(random.uniform(15.0, 25.0), 1)
                prod.calories = (prod.protein_grams * 4) + (prod.fat_grams * 9) + (prod.carbs_grams * 4)
                
            elif 'yogurt' in cat_name or 'lácteo' in cat_name:
                # Moderado
                prod.protein_grams = random.randint(8, 15)
                prod.fat_grams = round(random.uniform(0.0, 4.0), 1)
                prod.carbs_grams = round(random.uniform(5.0, 12.0), 1)
                prod.calories = (prod.protein_grams * 4) + (prod.fat_grams * 9) + (prod.carbs_grams * 4)
                
            else:
                # Genérico / Otros
                prod.protein_grams = random.randint(1, 10)
                prod.fat_grams = round(random.uniform(1.0, 10.0), 1)
                prod.carbs_grams = round(random.uniform(10.0, 30.0), 1)
                prod.calories = (prod.protein_grams * 4) + (prod.fat_grams * 9) + (prod.carbs_grams * 4)

            prod.save()
            self.stdout.write(f"Actualizado: {prod.name} -> {prod.calories} kcal")
            count += 1

        if count == 0:
            self.stdout.write(self.style.WARNING("No se encontraron productos sin información nutricional (o todos tienen > 0 kcal)."))
        else:
            self.stdout.write(self.style.SUCCESS(f"¡Listo! Se actualizaron {count} productos con datos nutricionales."))
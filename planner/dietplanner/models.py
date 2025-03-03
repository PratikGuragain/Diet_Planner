from django.db import models
from django.core.validators import MinValueValidator

class Food(models.Model):
    name = models.CharField(max_length=200)
    calorie_count = models.IntegerField()
    image = models.ImageField(upload_to='food_images/', null=True, blank=True)

    def __str__(self):
        return self.name

class PendingFood(models.Model):
    food = models.OneToOneField(Food, on_delete=models.CASCADE, primary_key=True)
    ready_time = models.TimeField()
    cooked_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.food.name

class Ingredient(models.Model):
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='ingredients')
    name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=50, default='grams')

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"

class Inventory(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50)
    minimum_quantity = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.ingredient.name} - {self.quantity} {self.unit}"

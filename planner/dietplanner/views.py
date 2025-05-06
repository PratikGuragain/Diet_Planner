from django.shortcuts import render, redirect, get_object_or_404
from .models import Food, PendingFood, Ingredient, Inventory
from datetime import time, datetime
from django.core.mail import send_mail, BadHeaderError
from django.db.models import F
from django.utils import timezone
from decimal import Decimal
from planner.settings import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
import re
from twilio.rest import Client
import requests

TWILIO_ACCOUNT_SID = 'AC9a1ec0e1ceb7088ab9e4b938f4807585'
TWILIO_AUTH_TOKEN = '8ed9810e87cf83ade5e214da3c4839a8'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

try:
    account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
    print(f"Authenticated as: {account.friendly_name}")
except Exception as e:
    print(f"Authentication failed: {e}")
    
def dish_of_the_day():
    url = 'https://www.themealdb.com/api/json/v1/1/random.php'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        meal = data['meals'][0]
        return {
            'name': meal['strMeal'],
            'category': meal['strCategory'],
            'area': meal['strArea'],
            'instructions': meal['strInstructions'],
            'image': meal['strMealThumb'],
            'youtube': meal['strYoutube'],
        }
    return None

def home(request):
    dish = dish_of_the_day()
    return render(request, 'home.html', {'dish': dish})

def food_overview(request):
    pending_foods = PendingFood.objects.all()

    if request.method == 'POST': 
        name = request.POST.get('name')
        calorie_count = request.POST.get('calorie_count')
        image = request.FILES.get('image')
        ready_time_str = request.POST.get('ready_time')
        ingredients_str = request.POST.get('ingredients')
        user_whatsapp_number = request.POST.get('user_number')

        try:
            # Convert time from string to Python time object
            ready_time_obj = datetime.strptime(ready_time_str, '%I:%M %p').time()
            food = Food.objects.create(name=name, calorie_count=calorie_count, image=image)

            pending_food = PendingFood(food=food, ready_time=ready_time_obj)
            pending_food.save()

            if ingredients_str:
                ingredients_list = ingredients_str.split(',')
                for ingredient_data in ingredients_list:
                    parts = ingredient_data.split(':')
                    ingredient_name = parts[0].strip()
                    quantity = 1.0
                    unit = 'grams'

                    if len(parts) > 1:
                        quantity_unit = parts[1].strip()
                        try:
                            # Use regex to extract number and unit
                            quantity_str = re.search(r'^-?\d+(\.\d+)?', quantity_unit).group(0)
                            quantity = float(quantity_str)
                            unit_str = ''.join(filter(str.isalpha, quantity_unit.replace(quantity_str, '')))
                            if unit_str:
                                unit = unit_str
                        except (ValueError, AttributeError):
                            quantity = 1.0
                            unit = 'grams'

                    # Create ingredient record
                    ingredient = Ingredient.objects.create(food=food, name=ingredient_name, quantity=quantity, unit=unit)

                    # Manage inventory
                    try:
                        inventory_item = Inventory.objects.get(ingredient__name=ingredient.name)
                        inventory_item.quantity += Decimal(ingredient.quantity)
                        inventory_item.save()
                    except Inventory.DoesNotExist:
                        min_quantity = 1 if Decimal(ingredient.quantity) < 0 else 0
                        Inventory.objects.create(ingredient=ingredient, quantity=Decimal(ingredient.quantity), unit=ingredient.unit, minimum_quantity=min_quantity)

            # Send WhatsApp notification (if Twilio is configured)
            ingredients = Ingredient.objects.filter(food=food)
            ingredient_list = "\n".join([f"- {ing.name}: {ing.quantity} {ing.unit}" for ing in ingredients])
            message_body = f"Please prepare {food.name} by {ready_time_obj.strftime('%I:%M %p')}.\nIngredients:\n{ingredient_list}"

            if 'client' in globals():
                try:
                    message = client.messages.create(
                        from_='whatsapp:+14155238886',
                        body=message_body,
                        to=f'whatsapp:+{user_whatsapp_number}'
                    )
                    print(f"WhatsApp message sent: {message.sid}")
                except Exception as e:
                    print(f"Error sending WhatsApp message: {e}")
            else:
                print("Twilio client is not configured. WhatsApp message was not sent.")

            return redirect('food_overview')

        except ValueError as e:
            error_message = f"Invalid ready time or ingredient format. Error: {e}"
            return render(request, 'food_overview.html', {'pending_foods': pending_foods, 'error_message': error_message})

    return render(request, 'food_overview.html', {'pending_foods': pending_foods})

def cooked_food(request, id):
    try:
        pending_food = PendingFood.objects.get(food_id=id)
        if request.method == 'POST':
            cooked_time_str = request.POST.get('cooked_time')
            try:
                cooked_time_naive = datetime.strptime(cooked_time_str, '%Y-%m-%dT%H:%M')
                cooked_time = timezone.make_aware(cooked_time_naive)
                pending_food.cooked_time = cooked_time
                pending_food.save()

                # Update inventory
                ingredients = Ingredient.objects.filter(food=pending_food.food)
                for ing in ingredients:
                    try:
                        inventory_item = Inventory.objects.get(ingredient__name=ing.name)
                        inventory_item.quantity = F('quantity') - ing.quantity
                        inventory_item.save()
                    except Inventory.DoesNotExist:
                        pass

                return redirect('food_overview')
            except ValueError:
                error_message = "Invalid cooked time format. Please use শতাংশ-MM-DDTHH:MM."
                pending_foods = PendingFood.objects.all()
                return render(request, 'food_overview.html', {'pending_foods': pending_foods, 'error_message': error_message})
    except PendingFood.DoesNotExist:
        pass
    return redirect('food_overview')

def delete_pending_food(request, id):
    try:
        pending_food = PendingFood.objects.get(food_id=id)
        pending_food.delete()
    except PendingFood.DoesNotExist:
        pass
    return redirect('food_overview')

def food_list(request):
    foods = Food.objects.all()
    return render(request, 'food_list.html', {'foods': foods})

def add_food(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        calorie_count = request.POST.get('calorie_count')
        image = request.FILES.get('image')
        ingredients_str = request.POST.get('ingredients')

        food = Food.objects.create(name=name, calorie_count=calorie_count, image=image)

        if ingredients_str:
            ingredients_list = ingredients_str.split(',')
            for ingredient_data in ingredients_list:
                parts = ingredient_data.split(':')
                ingredient_name = parts[0].strip()
                quantity = 1.0
                unit = 'grams'

                if len(parts) > 1:
                    quantity_unit = parts[1].strip()
                    try:
                        quantity_str = ''.join(filter(str.isdigit, quantity_unit))
                        quantity = float(quantity_str)
                        unit_str = ''.join(filter(str.isalpha, quantity_unit))
                        if unit_str:
                            unit = unit_str
                    except ValueError:
                        quantity = 1.0
                        unit = 'grams'

                ingredient = Ingredient.objects.create(food=food, name=ingredient_name, quantity=quantity, unit=unit)

                # Add or update inventory
                try:
                    inventory_item = Inventory.objects.get(ingredient__name=ingredient.name)
                    inventory_item.quantity += Decimal(ingredient.quantity)
                    inventory_item.save()
                except Inventory.DoesNotExist:
                    Inventory.objects.create(ingredient=ingredient, quantity=Decimal(ingredient.quantity), unit=ingredient.unit, minimum_quantity=0)

        return redirect('food_list')
    return render(request, 'add_food.html')

def view_food(request):
    foods = Food.objects.all()
    return render(request, 'view_food.html', {'foods': foods})

def ingredients_book(request):
    foods = Food.objects.all()
    return render(request, 'ingredients_book.html', {'foods': foods})

def delete_food(request, id):
    try:
        food = Food.objects.get(id=id)
        food.delete()
    except Food.DoesNotExist:
        pass
    return redirect('food_list')

def inventory_list(request):
    inventory_items = Inventory.objects.all()
    return render(request, 'inventory_list.html', {'inventory_items': inventory_items})

def reorder_list(request):
    reorder_items = Inventory.objects.filter(quantity__lt=F('minimum_quantity'))
    return render(request, 'reorder_list.html', {'reorder_items': reorder_items})

def delete_inventory_item(request, id):
    item = get_object_or_404(Inventory, id=id)
    item.delete()
    return redirect('reorder_list')


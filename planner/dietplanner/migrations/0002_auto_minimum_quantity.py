from django.db import migrations

def set_minimum_quantity(apps, schema_editor):
    Inventory = apps.get_model('dietplanner', 'Inventory')
    for item in Inventory.objects.all():
        item.minimum_quantity = 1
        item.save()

class Migration(migrations.Migration):

    dependencies = [
        ('dietplanner', '0001_initial'),  # Replace with your previous migration file name
    ]

    operations = [
        migrations.RunPython(set_minimum_quantity),
    ]
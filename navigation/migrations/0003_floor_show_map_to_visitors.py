from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('navigation', '0002_location_area_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='floor',
            name='show_map_to_visitors',
            field=models.BooleanField(
                default=True,
                help_text="When OFF, visitors see only nodes/connections — the floor plan image is hidden.",
            ),
        ),
    ]

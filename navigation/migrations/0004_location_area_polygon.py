from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('navigation', '0003_floor_show_map_to_visitors'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='area_polygon',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='List of [x_pct, y_pct] polygon vertices drawn by admin on the floor map.',
            ),
        ),
    ]

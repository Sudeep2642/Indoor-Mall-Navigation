from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('navigation', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='area_size',
            field=models.CharField(
                choices=[
                    ('xs', 'XS — Tiny (kiosk / ATM)'),
                    ('sm', 'Small (≤ 200 sq ft)'),
                    ('md', 'Medium (200–600 sq ft)'),
                    ('lg', 'Large (600–1500 sq ft)'),
                    ('xl', 'XL — Anchor (1500 sq ft +)'),
                ],
                default='md',
                max_length=4,
            ),
        ),
    ]

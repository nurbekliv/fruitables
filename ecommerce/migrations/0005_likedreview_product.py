# Generated by Django 5.1.1 on 2024-10-03 17:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0004_alter_likedreview_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='likedreview',
            name='product',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='ecommerce.product'),
            preserve_default=False,
        ),
    ]

# Generated by Django 5.1.1 on 2024-10-08 09:48

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0006_order_orderitem'),
    ]

    operations = [
        migrations.RenameField(
            model_name='orderitem',
            old_name='total_price',
            new_name='price',
        ),
        migrations.AlterField(
            model_name='order',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.DeleteModel(
            name='ProductSales',
        ),
    ]

# Generated by Django 4.2 on 2024-03-16 07:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('myapp', '0002_alter_rentedroom_remarks_alter_room_available'),
    ]

    operations = [
        migrations.AddField(
            model_name='rentedroom',
            name='offered_rent',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
        migrations.AddField(
            model_name='room',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='documentupload',
            name='document_type',
            field=models.CharField(choices=[('CITIZENSHIP', 'Citizenship'), ('LICENCE', 'Licence')], max_length=200),
        ),
        migrations.AlterField(
            model_name='rentedroom',
            name='status',
            field=models.CharField(choices=[('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected'), ('PENDING', 'Pending'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=10),
        ),
        migrations.AlterField(
            model_name='rentedroom',
            name='tenant_id',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='tenant', to=settings.AUTH_USER_MODEL),
        ),
    ]
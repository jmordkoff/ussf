# Generated by Django 2.0.1 on 2018-05-24 01:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ussfreg', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='fifa_id',
            field=models.CharField(blank=True, max_length=32, null=True, verbose_name='fifa-id'),
        ),
        migrations.AlterField(
            model_name='competition',
            name='ussf_submitted',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='player',
            name='gender',
            field=models.CharField(choices=[('m', 'male'), ('f', 'female')], max_length=1, verbose_name='gender'),
        ),
        migrations.AlterField(
            model_name='player',
            name='ussf_submitted',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

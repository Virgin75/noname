# Generated by Django 4.2.4 on 2023-10-26 19:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('contacts', '0006_alter_segment_filters'),
    ]

    operations = [
        migrations.CreateModel(
            name='Filter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('filter_type', models.CharField(choices=[('email', 'Email'), ('fields', 'Custom field')], default='email', max_length=20)),
                ('value', models.CharField(blank=True, max_length=100, null=True)),
                ('belongs_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.company')),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operator', models.CharField(choices=[('AND', 'all'), ('OR', 'any')], default='AND', max_length=3)),
                ('belongs_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.company')),
                ('filters', models.ManyToManyField(related_name='groups', to='contacts.filter')),
            ],
        ),
    ]

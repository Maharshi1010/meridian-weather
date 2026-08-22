from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SavedCity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('country', models.CharField(blank=True, max_length=10)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('session_key', models.CharField(db_index=True, max_length=40)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Saved cities',
                'ordering': ['-added_at'],
                'unique_together': {('name', 'country', 'session_key')},
            },
        ),
    ]

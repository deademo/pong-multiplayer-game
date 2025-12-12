# Generated migration

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MatchHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_code', models.CharField(db_index=True, max_length=50)),
                ('player1_score', models.IntegerField()),
                ('player2_score', models.IntegerField()),
                ('winner', models.CharField(max_length=20)),
                ('points_limit', models.IntegerField()),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name_plural': 'Match Histories',
                'ordering': ['-created_at'],
            },
        ),
    ]

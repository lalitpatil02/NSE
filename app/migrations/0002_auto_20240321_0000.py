from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='corporatefiling',
            old_name='announcement_date',
            new_name='filing_date',
        ),
        migrations.AddField(
            model_name='corporatefiling',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='corporatefiling',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
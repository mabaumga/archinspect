# Generated manually for prompt text versioning

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('persistence', '0003_serviceendpoint_qualityanalysis'),
    ]

    operations = [
        migrations.AddField(
            model_name='promptrun',
            name='prompt_text_snapshot',
            field=models.TextField(default='', help_text='Snapshot of prompt text at execution time for auditability'),
            preserve_default=False,
        ),
    ]

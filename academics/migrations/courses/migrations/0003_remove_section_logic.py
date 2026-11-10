# courses/migrations/0003_remove_section_logic.py
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_alter_courseoffering_options_and_more'), # Depends on the broken one being skipped/replaced
        ('staff', '0001_initial'),
    ]

    operations = [
        # 1. Remove the section field from LecturerAssignment
        migrations.RemoveField(
            model_name='lecturerassignment',
            name='section',
        ),
        # 2. Delete the Section model entirely
        migrations.DeleteModel(
            name='Section',
        ),
    ]
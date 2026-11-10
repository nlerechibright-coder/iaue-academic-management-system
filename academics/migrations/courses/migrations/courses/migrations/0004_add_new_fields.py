# courses/migrations/0004_add_new_fields.py
import django.core.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_remove_section_logic'),
        ('academics', '0002_alter_academicsession_options_alter_semester_options_and_more'),
        ('institution', '0001_initial'),
    ]

    operations = [
        # 1. Add assigned_at with a valid default
        migrations.AddField(
            model_name='lecturerassignment',
            name='assigned_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        # 2. Update credit_units validators
        migrations.AlterField(
            model_name='course',
            name='credit_units',
            field=models.IntegerField(default=3, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(6)]),
        ),
        # 3. Update prerequisites relation
        migrations.AlterField(
            model_name='course',
            name='prerequisites',
            field=models.ManyToManyField(blank=True, related_name='dependent_courses', to='courses.course'),
        ),
        # 4. Fix Unique Together for Course
        migrations.AlterUniqueTogether(
            name='course',
            unique_together={('code', 'department', 'level', 'semester')},
        ),
        # 5. Fix Unique Together for LecturerAssignment (now without section)
        migrations.AlterUniqueTogether(
            name='lecturerassignment',
            unique_together={('offering', 'lecturer')},
        ),
        # 6. Update Ordering
        migrations.AlterModelOptions(
            name='lecturerassignment',
            options={'ordering': ['-assigned_at']},
        ),
        migrations.AlterModelOptions(
            name='courseoffering',
            options={'ordering': ['session__name', 'course__code'], 'verbose_name_plural': 'Course Offerings'},
        ),
    ]
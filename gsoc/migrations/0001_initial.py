# Generated by Django 2.1.7 on 2019-02-13 10:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import gsoc.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GSoC',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('C', 'Completed (3rd Evaluation)'), ('2', 'Second Evaluation'), ('1', 'First Evaluation'), ('S', 'Selected'), ('A', 'Applied'), ('T', 'Trying'), ('M', 'Mentored')], default='T', max_length=1)),
                ('year', models.IntegerField()),
                ('proposal', models.FileField(blank=True, null=True, upload_to=gsoc.models.GSoC.get_proposal_link, verbose_name='Attach Proposal')),
                ('link', models.URLField(blank=True, max_length=150, null=True, verbose_name='External URL')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='GSoC', to=settings.AUTH_USER_MODEL, verbose_name='Member')),
            ],
            options={
                'verbose_name': 'GSoC',
                'verbose_name_plural': 'GSoCs',
            },
        ),
    ]

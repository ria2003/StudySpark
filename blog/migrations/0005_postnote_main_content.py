# Generated by Django 5.1.2 on 2025-02-10 14:09

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='postnote',
            name='main_content',
            field=ckeditor.fields.RichTextField(blank=True, null=True),
        ),
    ]

# Generated by Django 3.1.14 on 2022-09-25 07:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20220925_0728'),
    ]

    operations = [
        migrations.RenameField(
            model_name='post',
            old_name='image1',
            new_name='image',
        ),
        migrations.RemoveField(
            model_name='post',
            name='image2',
        ),
        migrations.RemoveField(
            model_name='post',
            name='image3',
        ),
        migrations.RemoveField(
            model_name='post',
            name='image4',
        ),
    ]

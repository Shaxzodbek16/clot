# Generated by Django 5.1.4 on 2024-12-20 06:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0002_onetimepassword"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="onetimepassword",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "One Time Password",
                "verbose_name_plural": "One Time Passwords",
            },
        ),
        migrations.RemoveField(
            model_name="onetimepassword",
            name="expiry",
        ),
        migrations.RemoveField(
            model_name="onetimepassword",
            name="purpose",
        ),
        migrations.AlterModelTable(
            name="onetimepassword",
            table="otp",
        ),
    ]
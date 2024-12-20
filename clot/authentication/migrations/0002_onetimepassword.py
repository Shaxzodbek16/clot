# Generated by Django 5.1.4 on 2024-12-20 04:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OneTimePassword",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("passcode", models.CharField(max_length=6)),
                ("purpose", models.CharField(default="verification", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expiry", models.DateTimeField(blank=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="otps",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "One Time Password",
                "verbose_name_plural": "One Time Passwords",
            },
        ),
    ]

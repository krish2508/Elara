import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Creates the refresh_tokens table under the accounts app.

    Note: if you ran users.0003_delete_refreshtoken before this migration,
    the table was dropped — this migration recreates it.
    If the table already exists (fresh DB), this creates it for the first time.
    """

    dependencies = [
        ("users", "0003_delete_refreshtoken"),
    ]

    operations = [
        migrations.CreateModel(
            name="RefreshToken",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="refresh_tokens",
                        to="users.usermaindetails",
                    ),
                ),
                ("jti", models.CharField(db_index=True, max_length=64, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("revoked", models.BooleanField(default=False)),
                ("user_agent", models.TextField(blank=True, null=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Refresh Token",
                "verbose_name_plural": "Refresh Tokens",
                "db_table": "refresh_tokens",
            },
        ),
    ]

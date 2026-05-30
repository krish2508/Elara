import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Originally this migration also created the RefreshToken table.
    That model has been moved to apps.accounts — see accounts 0001 migration.
    The DB table (refresh_tokens) already exists; we use SeparateDatabaseAndState
    to keep Django's state in sync without touching the DB again.
    """

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        # Add is_active to UserMainDetails
        migrations.AddField(
            model_name="usermaindetails",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        # Add password_hash to UserMainDetails
        migrations.AddField(
            model_name="usermaindetails",
            name="password_hash",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        # RefreshToken table was created here originally but the model now lives
        # in apps.accounts. The accounts 0001 migration owns it going forward.
        # We use SeparateDatabaseAndState so Django's migration state reflects
        # the move without issuing a duplicate CREATE TABLE.
        migrations.SeparateDatabaseAndState(
            database_operations=[],  # table already exists in DB — do nothing
            state_operations=[
                migrations.CreateModel(
                    name="RefreshToken",
                    fields=[
                        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="refresh_tokens", to="users.usermaindetails")),
                        ("jti", models.CharField(db_index=True, max_length=64, unique=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("expires_at", models.DateTimeField()),
                        ("revoked", models.BooleanField(default=False)),
                        ("user_agent", models.TextField(blank=True, null=True)),
                        ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                    ],
                    options={"verbose_name": "Refresh Token", "verbose_name_plural": "Refresh Tokens", "db_table": "refresh_tokens"},
                ),
            ],
        ),
    ]

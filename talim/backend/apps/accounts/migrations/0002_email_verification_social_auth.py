from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="email_verification_code",
            field=models.CharField(blank=True, max_length=6),
        ),
        migrations.AddField(
            model_name="user",
            name="email_verification_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="auth_provider",
            field=models.CharField(
                choices=[("password", "Parol"), ("google", "Google"), ("facebook", "Facebook"), ("apple", "Apple")],
                default="password",
                max_length=20,
            ),
        ),
    ]

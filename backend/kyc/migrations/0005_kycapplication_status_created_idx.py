from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("kyc", "0004_alter_kycapplication_status_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="kycapplication",
            index=models.Index(
                fields=["status", "-created_at"], name="kyc_app_status_created_idx"
            ),
        ),
    ]

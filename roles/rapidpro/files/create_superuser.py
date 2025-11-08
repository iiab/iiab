import os
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

User = get_user_model()

email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "changeme")

try:
    User.objects.get(email=email)
    print("Superuser already exists.")
except ObjectDoesNotExist:
    u = User.objects.create_user(email=email, password=password)
    u.is_superuser = True
    u.is_staff = True
    u.save()
    print("Superuser created successfully!")

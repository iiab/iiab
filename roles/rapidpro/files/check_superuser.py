import os
from django.contrib.auth import get_user_model

User = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
if User.objects.filter(email=email).exists():
    print("EXISTS")

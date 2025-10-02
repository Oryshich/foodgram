from django.contrib.auth.models import BaseUserManager
from django.db.models import Q


class UserManager(BaseUserManager):
    def create_user(
            self,
            email,
            username,
            first_name,
            last_name,
            password=None,
            **extra_fields
    ):
        if not email:
            raise ValueError('Email не заполнен')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
            self,
            email,
            username,
            first_name,
            last_name,
            password=None,
            **extra_fields
    ):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if (extra_fields.get('is_staff') is not True
                or extra_fields.get('is_superuser') is not True):
            raise ValueError(
                'Для superuser is_staff=True, is_superuser=True'
            )
        return self.create_user(
            email,
            username,
            first_name,
            last_name,
            password,
            **extra_fields
        )

    def get_by_natural_key(self, email):
        return self.get(Q(email__iexact=email))

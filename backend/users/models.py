from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q

from .constants import (MAX_LENGTH_EMAIL, MAX_LENGTH_FIRST_NAME,
                        MAX_LENGTH_LAST_NAME, MAX_LENGTH_USERNAME)


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


class User(AbstractBaseUser):
    """Модель пользователя с идентификацией по email."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name'
    ]

    username = models.CharField(
        max_length=MAX_LENGTH_USERNAME,
        unique=True,
        validators=[RegexValidator(regex=r'^[\w.@+-]+\Z')],
        verbose_name='Имя пользователя',
        help_text='Только буквы, цифры, символ подчёркивания, '
                  'точка, «@», плюс или дефис.'
    )
    email = models.EmailField(
        verbose_name='email адрес (login)',
        max_length=MAX_LENGTH_EMAIL,
        unique=True,
        help_text='Адрес электронной почты.'
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_FIRST_NAME,
        verbose_name='Имя пользователя',
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_LAST_NAME,
        verbose_name='Фамилия пользователя',
    )
    avatar = models.ImageField(
        verbose_name='Изображение профиля',
        null=True,
        blank=True,
        upload_to='users/images/',
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return f'Пользователь: {self.username}, email: {self.email}'

    def has_module_perms(self, app_label):
        return self.is_active

    def has_perm(self, perm, obj=None):
        return self.is_active


class Subscriptions(models.Model):
    """Модель подписки на автора рецепта."""

    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='follows',
    )
    following = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='followers',
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('following',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_pair_user_following',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='prevent_self_follow',
            ),
        ]

    def __str__(self):
        return (f'{self.user.username} подписан на {self.following.username}')

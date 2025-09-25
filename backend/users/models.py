from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .constants import (
    MAX_LENGTH_EMAIL,
    MAX_LENGTH_FIRST_NAME,
    MAX_LENGTH_LAST_NAME,
    MAX_LENGTH_PASSWORD,
    MAX_LENGTH_USERNAME
)


class User(AbstractUser):
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
    password = models.CharField(
        max_length=MAX_LENGTH_PASSWORD,
        verbose_name='Пароль'
    )
    avatar = models.ImageField(
        verbose_name='Изображение профиля',
        null=True,
        blank=True,
        upload_to='users/images/',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self) -> str:
        return f'Пользователь: {self.username}, email: {self.email}'


class Follow(models.Model):
    """Модель подписки на автора рецепта."""

    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='subscriber',
    )
    following = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='following',
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
        return (f'{self.user} подписан на {self.following}')

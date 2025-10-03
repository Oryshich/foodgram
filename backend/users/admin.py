from itertools import chain

from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'user_subscriptions',
        'user_favorites',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name'
    )
    list_filter = ('username', 'email')
    ordering = ('id',)

    @admin.display(description='Подписки')
    def user_subscriptions(self, object):
        data = object.follows.values_list('following__username')
        return list(chain.from_iterable(data))

    @admin.display(description='Избранное')
    def user_favorites(self, object):
        data = object.followers.values_list('user__username')
        return list(chain.from_iterable(data))

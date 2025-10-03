from itertools import chain

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from .models import User


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)


# class UserAdmin(admin.ModelAdmin):
@admin.register(User)
class UserAdmin(BaseUserAdmin):
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

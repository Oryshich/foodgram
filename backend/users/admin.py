from django.contrib import admin
# from django.contrib.auth.models import Group

from .models import Follow, User

# admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name'
    )
    list_filter = ('username', 'email')
    ordering = ('id',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')

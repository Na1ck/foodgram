from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Subscription


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'author__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

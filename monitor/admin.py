from django.contrib import admin
from .models import Website, HealthCheck, Alert, NotificationChannel


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'status', 'is_active', 'uptime_percentage', 'last_check']
    list_filter = ['status', 'is_active', 'created_at']
    search_fields = ['name', 'url']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_check', 'uptime_percentage']
    
    fieldsets = (
        ('Информация', {
            'fields': ('id', 'user', 'name', 'url')
        }),
        ('Настройки проверки', {
            'fields': ('check_interval', 'timeout', 'is_active')
        }),
        ('Статус', {
            'fields': ('status', 'last_check', 'last_response_time', 'uptime_percentage')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(HealthCheck)
class HealthCheckAdmin(admin.ModelAdmin):
    list_display = ['website', 'status', 'status_code', 'response_time', 'checked_at']
    list_filter = ['status', 'checked_at']
    search_fields = ['website__name', 'error_message']
    readonly_fields = ['checked_at']
    
    fieldsets = (
        ('Информация', {
            'fields': ('website', 'status', 'status_code')
        }),
        ('Результаты', {
            'fields': ('response_time', 'error_message', 'checked_at')
        }),
    )


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['website', 'alert_type', 'status', 'triggered_at']
    list_filter = ['alert_type', 'status', 'triggered_at']
    search_fields = ['website__name', 'message']
    readonly_fields = ['triggered_at']
    
    fieldsets = (
        ('Информация', {
            'fields': ('website', 'alert_type', 'status')
        }),
        ('Сообщение', {
            'fields': ('message',)
        }),
        ('Временные метки', {
            'fields': ('triggered_at', 'acknowledged_at', 'resolved_at')
        }),
    )


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ['user', 'channel_type', 'is_active', 'created_at']
    list_filter = ['channel_type', 'is_active']
    search_fields = ['user__username']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Информация', {
            'fields': ('user', 'channel_type', 'is_active')
        }),
        ('Конфигурация', {
            'fields': ('config',)
        }),
        ('Метаданные', {
            'fields': ('created_at',)
        }),
    )

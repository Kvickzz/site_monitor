from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Website(models.Model):
    STATUS_CHOICES = [
        ('up', 'Работает'),
        ('down', 'Не работает'),
        ('slow', 'Работает медленно'),
        ('unknown', 'Неизвестно'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='websites')
    name = models.CharField(max_length=255)
    url = models.URLField()
    
    check_interval = models.IntegerField(default=300)
    timeout = models.IntegerField(default=10)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unknown')
    is_active = models.BooleanField(default=True)
    
    uptime_percentage = models.FloatField(default=100.0)
    last_check = models.DateTimeField(null=True, blank=True)
    last_response_time = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.url})"
    
    @property
    def is_up(self):
        return self.status == 'up'


class HealthCheck(models.Model):
    STATUS_CHOICES = [
        ('success', 'Успех'),
        ('timeout', 'Таймаут'),
        ('error', 'Ошибка'),
        ('ssl_error', 'Ошибка SSL'),
        ('connection_error', 'Ошибка соединения'),
    ]
    
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='health_checks')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    status_code = models.IntegerField(null=True, blank=True)
    response_time = models.FloatField()
    
    error_message = models.TextField(blank=True)
    checked_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['website', '-checked_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.website.name} - {self.status} ({self.checked_at})"


class Alert(models.Model):
    ALERT_TYPES = [
        ('down', 'Сайт не работает'),
        ('up', 'Сайт восстановлен'),
        ('slow', 'Сайт работает медленно'),
        ('ssl_error', 'Ошибка SSL'),
    ]
    
    STATUS_CHOICES = [
        ('triggered', 'Активно'),
        ('acknowledged', 'Принято'),
        ('resolved', 'Решено'),
    ]
    
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='triggered')
    
    message = models.TextField()
    triggered_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-triggered_at']
        indexes = [
            models.Index(fields=['website', 'status']),
            models.Index(fields=['alert_type']),
        ]
    
    def __str__(self):
        return f"{self.website.name} - {self.alert_type}"


class NotificationChannel(models.Model):
    CHANNEL_TYPES = [
        ('email', 'Email'),
        ('telegram', 'Telegram'),
        ('slack', 'Slack'),
        ('webhook', 'Webhook'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_channels')
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    
    config = models.JSONField(default=dict)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'channel_type',)
    
    def __str__(self):
        return f"{self.user.username} - {self.channel_type}"

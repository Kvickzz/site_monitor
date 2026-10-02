from rest_framework import serializers
from .models import Website, HealthCheck, Alert, NotificationChannel
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class HealthCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthCheck
        fields = [
            'id', 'website', 'status', 'status_code',
            'response_time', 'error_message', 'checked_at'
        ]
        read_only_fields = ['id', 'checked_at']


class AlertSerializer(serializers.ModelSerializer):
    website_name = serializers.CharField(source='website.name', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'website', 'website_name', 'alert_type',
            'status', 'message', 'triggered_at',
            'acknowledged_at', 'resolved_at'
        ]
        read_only_fields = ['id', 'triggered_at']


class WebsiteSerializer(serializers.ModelSerializer):
    health_checks = HealthCheckSerializer(many=True, read_only=True)
    alerts = AlertSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    
    last_check_ago = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Website
        fields = [
            'id', 'user', 'name', 'url', 'check_interval',
            'timeout', 'status', 'status_display', 'is_active',
            'uptime_percentage', 'last_check', 'last_check_ago',
            'last_response_time', 'created_at', 'updated_at',
            'health_checks', 'alerts'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_last_check_ago(self, obj):
        if not obj.last_check:
            return 'Никогда'
        
        from django.utils.timezone import now
        from datetime import timedelta
        
        delta = now() - obj.last_check
        
        if delta < timedelta(minutes=1):
            return 'Только что'
        elif delta < timedelta(hours=1):
            minutes = delta.total_seconds() // 60
            return f'{int(minutes)} мин назад'
        elif delta < timedelta(days=1):
            hours = delta.total_seconds() // 3600
            return f'{int(hours)} час назад'
        else:
            days = delta.days
            return f'{days} дн назад'


class NotificationChannelSerializer(serializers.ModelSerializer):
    channel_type_display = serializers.CharField(
        source='get_channel_type_display',
        read_only=True
    )
    
    class Meta:
        model = NotificationChannel
        fields = [
            'id', 'channel_type', 'channel_type_display',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

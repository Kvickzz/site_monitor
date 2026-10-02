from celery import shared_task, chunks
from django.utils import timezone
from django.core.cache import cache
from .models import Website, HealthCheck, Alert
from .services import HealthCheckService
import logging
from datetime import timedelta
from django.db.models import F, Q

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, ignore_result=True)
def check_website_health(self, website_ids):
    for website_id in website_ids:
        _check_single_website(website_id)


def _check_single_website(website_id):
    try:
        website = Website.objects.get(id=website_id)
    except Website.DoesNotExist:
        logger.error(f"Website with id {website_id} not found")
        return

    if not website.is_active:
        return

    service = HealthCheckService()
    result = service.check_website(website)

    HealthCheck.objects.create(
        website=website,
        status=result['status'],
        status_code=result.get('status_code'),
        response_time=result['response_time'],
        error_message=result.get('error_message', '')
    )

    old_status = website.status
    website.status = determine_website_status(result)
    website.last_check = timezone.now()
    website.last_response_time = result['response_time']
    website.save()

    if old_status != website.status:
        create_status_change_alert(website, old_status, website.status)
        
        cache.set(f'website_status_{website_id}', {
            'status': website.status,
            'response_time': website.last_response_time,
            'last_check': timezone.now()
        }, timeout=website.check_interval)
        
        logger.info(f"Health check completed for {website.name}: {website.status}")
        return f"Website {website.name} checked: {website.status}"
        
        
@shared_task
def check_all_websites():
    now = timezone.now()

    due = Website.objects.filter(is_active=True).filter(
        Q(last_check__isnull=True) |
        Q(last_check__lte=now - timedelta(seconds=1) * F('check_interval'))
    )
    ids = list(due.values_list('id', flat=True))

    if ids:
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            check_website_health.delay(ids[i:i + batch_size])

    logger.info(f"Scheduled health checks for {due.count()} websites")
    return f"Scheduled {due.count()} health checks"


@shared_task
def cleanup_old_health_checks(days=30):
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count, _ = HealthCheck.objects.filter(
        checked_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Deleted {deleted_count} old health check records")
    return f"Deleted {deleted_count} records"


@shared_task
def calculate_uptime_statistics():
    websites = Website.objects.all()
    
    for website in websites:
        total_checks = website.health_checks.count()
        
        if total_checks == 0:
            website.uptime_percentage = 100.0
        else:
            successful_checks = website.health_checks.filter(
                status='success'
            ).count()
            uptime = (successful_checks / total_checks) * 100
            website.uptime_percentage = round(uptime, 2)
        
        website.save()
    
    logger.info(f"Updated uptime statistics for {websites.count()} websites")
    return f"Updated statistics for {websites.count()} websites"


def determine_website_status(result):
    if result['status'] == 'success':
        if result['response_time'] > 5000:
            return 'slow'
        return 'up'
    return 'down'


@shared_task
def send_alert_notification(alert_id):
    from .services import NotificationService

    try:
        alert = Alert.objects.get(id=alert_id)
    except Alert.DoesNotExist:
        logger.error(f"Alert {alert_id} not found")
        return

    channels = alert.website.user.notification_channels.filter(is_active=True)
    service = NotificationService()

    for channel in channels:
        try:
            service.send_notification(channel, alert)
        except Exception as e:
            logger.error(f"Failed to send via {channel.channel_type}: {e}")


def create_status_change_alert(website, old_status, new_status):
    if old_status != new_status:
        if new_status == 'down':
            alert_type = 'down'
            message = f"Сайт {website.name} is now DOWN"
        elif new_status == 'up':
            alert_type = 'up'
            message = f"Сайт {website.name} is now UP"
        else:
            alert_type = 'slow'
            message = f"Сайт {website.name} is responding SLOWLY"
        
        alert = Alert.objects.create(
            website=website,
            alert_type=alert_type,
            message=message
        )
        send_alert_notification.delay(alert.id)
        logger.info(f"Alert created for {website.name}: {alert_type}")

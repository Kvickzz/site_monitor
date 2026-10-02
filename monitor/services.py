import requests
import time
import logging
from typing import Dict, Any
from requests.exceptions import (
    Timeout, ConnectionError, SSLError, RequestException
)
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


class HealthCheckService:
    
    def __init__(self):
        self.session = requests.Session()
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def check_website(self, website) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            response = self.session.head(
                website.url,
                timeout=website.timeout,
                allow_redirects=True,
                headers={'User-Agent': 'SiteMonitor/1.0'}
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 405:
                response = self.session.get(
                    website.url,
                    timeout=website.timeout,
                    allow_redirects=True,
                    headers={'User-Agent': 'SiteMonitor/1.0'}
                )
                response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'success',
                'status_code': response.status_code,
                'response_time': round(response_time, 2),
                'error_message': ''
            }
            
        except Timeout:
            response_time = (time.time() - start_time) * 1000
            logger.warning(f"Timeout checking {website.url} after {website.timeout}s")
            return {
                'status': 'timeout',
                'status_code': None,
                'response_time': response_time,
                'error_message': f'Request timeout after {website.timeout}s'
            }
        
        except SSLError as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"SSL error checking {website.url}: {str(e)}")
            return {
                'status': 'ssl_error',
                'status_code': None,
                'response_time': response_time,
                'error_message': f'SSL certificate error: {str(e)}'
            }
        
        except ConnectionError as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Connection error checking {website.url}: {str(e)}")
            return {
                'status': 'connection_error',
                'status_code': None,
                'response_time': response_time,
                'error_message': f'Connection error: {str(e)}'
            }
        
        except RequestException as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Request error checking {website.url}: {str(e)}")
            return {
                'status': 'error',
                'status_code': None,
                'response_time': response_time,
                'error_message': str(e)
            }
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error checking {website.url}: {str(e)}")
            return {
                'status': 'error',
                'status_code': None,
                'response_time': response_time,
                'error_message': f'Unexpected error: {str(e)}'
            }


class NotificationService:
    
    def send_notification(self, channel, alert):
        if channel.channel_type == 'email':
            self._send_email_notification(channel, alert)
        elif channel.channel_type == 'telegram':
            self._send_telegram_notification(channel, alert)
        elif channel.channel_type == 'slack':
            self._send_slack_notification(channel, alert)
        elif channel.channel_type == 'webhook':
            self._send_webhook_notification(channel, alert)
    
    def _send_email_notification(self, channel, alert):

        
        email = channel.config.get('email')
        if not email:
            return
        
        subject = f"Alert: {alert.website.name} - {alert.get_alert_type_display()}"
        message = f"""
        Website: {alert.website.name}
        URL: {alert.website.url}
        Status: {alert.get_alert_type_display()}
        Message: {alert.message}
        Time: {alert.triggered_at}
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        logger.info(f"Email notification sent to {email} for {alert.website.name}")
    
    def _send_telegram_notification(self, channel, alert):
        try:
            import requests
            
            chat_id = channel.config.get('chat_id')
            token = settings.TELEGRAM_BOT_TOKEN
            
            if not chat_id or not token:
                logger.error("Telegram credentials not configured")
                return
            
            message = f"""
            🚨 *Alert: {alert.website.name}*
            Status: {alert.get_alert_type_display()}
            URL: {alert.website.url}
            Message: {alert.message}
            Time: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data, timeout=5)
            response.raise_for_status()
            
            logger.info(f"Telegram notification sent for {alert.website.name}")
        
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {str(e)}")
            raise
    
    def _send_slack_notification(self, channel, alert):
        try:
            import requests
            
            webhook_url = channel.config.get('webhook_url')
            
            if not webhook_url:
                logger.error("Slack webhook URL not configured")
                return
            
            color = 'danger' if alert.alert_type == 'down' else 'warning'
            
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"Alert: {alert.website.name}",
                        "fields": [
                            {
                                "title": "Status",
                                "value": alert.get_alert_type_display(),
                                "short": True
                            },
                            {
                                "title": "URL",
                                "value": alert.website.url,
                                "short": True
                            },
                            {
                                "title": "Message",
                                "value": alert.message,
                                "short": False
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=5)
            response.raise_for_status()
            
            logger.info(f"Slack notification sent for {alert.website.name}")
        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            raise
    
    def _send_webhook_notification(self, channel, alert):
        try:
            import requests
            
            webhook_url = channel.config.get('url')
            
            if not webhook_url:
                logger.error("Webhook URL not configured")
                return
            
            payload = {
                'alert_id': alert.id,
                'website_id': str(alert.website.id),
                'website_name': alert.website.name,
                'url': alert.website.url,
                'alert_type': alert.alert_type,
                'message': alert.message,
                'timestamp': alert.triggered_at.isoformat()
            }
            
            response = requests.post(webhook_url, json=payload, timeout=5)
            response.raise_for_status()
            
            logger.info(f"Webhook notification sent for {alert.website.name}")
        
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {str(e)}")
            raise

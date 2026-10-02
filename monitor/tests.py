from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Website, HealthCheck, Alert
from .services import HealthCheckService
import uuid


class WebsiteModelTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_website(self):
        website = Website.objects.create(
            user=self.user,
            name='Test Site',
            url='https://example.com',
            check_interval=300
        )
        self.assertEqual(website.name, 'Test Site')
        self.assertEqual(website.status, 'unknown')
        self.assertTrue(website.is_active)
    
    def test_website_is_up_property(self):
        website = Website.objects.create(
            user=self.user,
            name='Test',
            url='https://example.com',
            status='up'
        )
        self.assertTrue(website.is_up)
        
        website.status = 'down'
        self.assertFalse(website.is_up)


class HealthCheckModelTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.website = Website.objects.create(
            user=self.user,
            name='Test',
            url='https://example.com'
        )
    
    def test_create_health_check(self):
        check = HealthCheck.objects.create(
            website=self.website,
            status='success',
            status_code=200,
            response_time=150.5
        )
        self.assertEqual(check.status, 'success')
        self.assertEqual(check.status_code, 200)


class AlertModelTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.website = Website.objects.create(
            user=self.user,
            name='Test',
            url='https://example.com'
        )
    
    def test_create_alert(self):
        alert = Alert.objects.create(
            website=self.website,
            alert_type='down',
            message='Website is down'
        )
        self.assertEqual(alert.alert_type, 'down')
        self.assertEqual(alert.status, 'triggered')


class DashboardViewTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_dashboard_requires_login(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
    
    def test_dashboard_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


class WebsiteListViewTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.website = Website.objects.create(
            user=self.user,
            name='Test',
            url='https://example.com'
        )
    
    def test_website_list_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/websites/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Website, HealthCheck, Alert, NotificationChannel
from .forms import WebsiteForm, NotificationSettingsForm
from .serializers import WebsiteSerializer, HealthCheckSerializer, AlertSerializer
from .tasks import check_website_health

@login_required
def dashboard(request):
    websites = Website.objects.filter(user=request.user).prefetch_related('health_checks')
    
    stats = {
        'total_websites': websites.count(),
        'up': websites.filter(status='up').count(),
        'down': websites.filter(status='down').count(),
        'slow': websites.filter(status='slow').count(),
        'unknown': websites.filter(status='unknown').count(),
    }
    
    recent_alerts = Alert.objects.filter(
        website__user=request.user,
        status='triggered'
    ).order_by('-triggered_at')[:10]
    
    context = {
        'websites': websites,
        'stats': stats,
        'recent_alerts': recent_alerts,
    }
    
    return render(request, 'monitor/dashboard.html', context)


@login_required
def website_list(request):
    websites = Website.objects.filter(user=request.user)
    
    status_filter = request.GET.get('status')
    if status_filter:
        websites = websites.filter(status=status_filter)
    
    search = request.GET.get('search')
    if search:
        websites = websites.filter(
            Q(name__icontains=search) | Q(url__icontains=search)
        )
    
    sort_by = request.GET.get('sort', '-created_at')
    websites = websites.order_by(sort_by)
    
    context = {
        'websites': websites,
        'status_filter': status_filter,
        'search': search,
    }
    
    return render(request, 'monitor/website_list.html', context)


@login_required
def website_detail(request, website_id):
    website = get_object_or_404(Website, id=website_id, user=request.user)
    
    health_checks = website.health_checks.all()[:100]
    
    now = timezone.now()
    
    stats = {
        '24h': get_uptime_for_period(website, 24),
        '7d': get_uptime_for_period(website, 7*24),
        '30d': get_uptime_for_period(website, 30*24),
    }
    
    avg_response_time = website.health_checks.filter(
        status='success'
    ).aggregate(avg=Avg('response_time'))['avg'] or 0
    
    recent_alerts = website.alerts.all()[:20]
    
    context = {
        'website': website,
        'health_checks': health_checks,
        'stats': stats,
        'avg_response_time': round(avg_response_time, 2),
        'recent_alerts': recent_alerts,
    }
    
    return render(request, 'monitor/website_detail.html', context)


@login_required
def add_website(request):
    if request.method == 'POST':
        form = WebsiteForm(request.POST)
        if form.is_valid():
            website = form.save(commit=False)
            website.user = request.user
            website.save()
            
            check_website_health.delay(str(website.id))
            
            messages.success(request, f'Сайт {website.name} добавлен')
            return redirect('monitor:website_detail', website_id=website.id)
    else:
        form = WebsiteForm()
    
    context = {'form': form}
    return render(request, 'monitor/add_website.html', context)


@login_required
def edit_website(request, website_id):
    website = get_object_or_404(Website, id=website_id, user=request.user)
    
    if request.method == 'POST':
        form = WebsiteForm(request.POST, instance=website)
        if form.is_valid():
            form.save()
            messages.success(request, 'Сайт обновлен')
            return redirect('monitor:website_detail', website_id=website.id)
    else:
        form = WebsiteForm(instance=website)
    
    context = {'form': form, 'website': website}
    return render(request, 'monitor/edit_website.html', context)


@login_required
@require_http_methods(["POST"])
def delete_website(request, website_id):
    website = get_object_or_404(Website, id=website_id, user=request.user)
    website.delete()
    messages.success(request, 'Сайт удален')
    return redirect('monitor:website_list')


@login_required
@require_http_methods(["POST"])
def toggle_monitoring(request, website_id):
    website = get_object_or_404(Website, id=website_id, user=request.user)
    website.is_active = not website.is_active
    website.save()
    
    status_text = 'включен' if website.is_active else 'отключен'
    messages.success(request, f'Мониторинг {status_text}')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_active': website.is_active})
    
    return redirect('monitor:website_detail', website_id=website.id)


@login_required
@require_http_methods(["POST"])
def run_check_now(request, website_id):
    website = get_object_or_404(Website, id=website_id, user=request.user)
    check_website_health.delay(str(website.id))
    messages.info(request, 'Проверка запущена')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'scheduled'})
    
    return redirect('monitor:website_detail', website_id=website.id)


@login_required
def statistics(request):
    websites = Website.objects.filter(user=request.user)
    
    total_checks = HealthCheck.objects.filter(
        website__user=request.user
    ).count()
    
    successful_checks = HealthCheck.objects.filter(
        website__user=request.user,
        status='success'
    ).count()
    
    overall_uptime = (successful_checks / total_checks * 100) if total_checks > 0 else 0
    
    most_reliable = websites.order_by('-uptime_percentage')[:5]
    most_problematic = websites.order_by('uptime_percentage')[:5]
    
    context = {
        'overall_uptime': round(overall_uptime, 2),
        'total_checks': total_checks,
        'websites': websites,
        'most_reliable': most_reliable,
        'most_problematic': most_problematic,
    }
    
    return render(request, 'monitor/statistics.html', context)


class WebsiteViewSet(viewsets.ModelViewSet):
    serializer_class = WebsiteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Website.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        check_website_health.delay(str(serializer.instance.id))
    
    @action(detail=True, methods=['post'])
    def check_now(self, request, pk=None):
        website = self.get_object()
        check_website_health.delay(str(website.id))
        return Response({'status': 'check_scheduled'})
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        website = self.get_object()
        website.is_active = not website.is_active
        website.save()
        return Response({'is_active': website.is_active})


class HealthCheckViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HealthCheckSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        website_id = self.request.query_params.get('website_id')
        if website_id:
            return HealthCheck.objects.filter(
                website__user=self.request.user,
                website__id=website_id
            )
        return HealthCheck.objects.filter(
            website__user=self.request.user
        )


class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Alert.objects.filter(
            website__user=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        alert.status = 'acknowledged'
        alert.acknowledged_at = timezone.now()
        alert.save()
        return Response({'status': 'acknowledged'})


def get_uptime_for_period(website, hours):
    since = timezone.now() - timedelta(hours=hours)
    
    checks = website.health_checks.filter(checked_at__gte=since)
    
    if not checks.exists():
        return None
    
    successful = checks.filter(status='success').count()
    total = checks.count()
    
    return round((successful / total) * 100, 2) if total > 0 else 0

class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'auth/register.html'
    success_url = reverse_lazy('monitor:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Аккаунт создан! Теперь войдите.')
        return response
    
    
@login_required
def profile(request):
    email_channel = NotificationChannel.objects.filter(user=request.user, channel_type='email').first()
    telegram_channel = NotificationChannel.objects.filter(user=request.user, channel_type='telegram').first()

    if request.method == 'POST':
        form = NotificationSettingsForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            if cd['email_enabled'] and cd['email_address']:
                NotificationChannel.objects.update_or_create(
                    user=request.user, channel_type='email',
                    defaults={'config': {'email': cd['email_address']}, 'is_active': True}
                )
            elif email_channel:
                email_channel.is_active = False
                email_channel.save()

            if cd['telegram_enabled'] and cd['telegram_chat_id']:
                NotificationChannel.objects.update_or_create(
                    user=request.user, channel_type='telegram',
                    defaults={'config': {'chat_id': cd['telegram_chat_id']}, 'is_active': True}
                )
            elif telegram_channel:
                telegram_channel.is_active = False
                telegram_channel.save()

            messages.success(request, 'Настройки уведомлений сохранены')
            return redirect('monitor:profile')
    else:
        form = NotificationSettingsForm(initial={
            'email_enabled': email_channel.is_active if email_channel else False,
            'email_address': email_channel.config.get('email', '') if email_channel else '',
            'telegram_enabled': telegram_channel.is_active if telegram_channel else False,
            'telegram_chat_id': telegram_channel.config.get('chat_id', '') if telegram_channel else '',
        })

    return render(request, 'monitor/profile.html', {'form': form})
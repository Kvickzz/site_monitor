from django import forms
from .models import Website, NotificationChannel


class WebsiteForm(forms.ModelForm):
    
    class Meta:
        model = Website
        fields = ['name', 'url', 'check_interval', 'timeout', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'check_interval': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '60',
                'max': '3600',
                'step': '60',
            }),
            'timeout': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '5',
                'max': '60',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Название сайта',
            'url': 'URL сайта',
            'check_interval': 'Интервал проверки (сек)',
            'timeout': 'Таймаут (сек)',
            'is_active': 'Включить мониторинг',
        }
    
    def clean_check_interval(self):
        interval = self.cleaned_data.get('check_interval')
        if interval and (interval < 60 or interval > 3600):
            raise forms.ValidationError('Интервал должен быть от 60 до 3600 секунд')
        return interval


class NotificationSettingsForm(forms.Form):
    email_enabled = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    email_address = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    telegram_enabled = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    telegram_chat_id = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
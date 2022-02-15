from django import forms
from django.forms import inlineformset_factory
from .models import Ticket, TicketNote

from django.db import models
from django.conf import settings
from datetime import datetime
from django.apps import apps
from libtekin.models import ItemRequest
from django.contrib.auth import get_user_model
from djmoney.models.fields import MoneyField

class ItemRequestForm(forms.ModelForm):
    class Meta:
        model = ItemRequest
        fields = [
            'description',
            'purpose',
            'notes',
            'price',
            'link',
            'substitutability',
            'urgency',
            'status',
            'submitted_by'
        ]


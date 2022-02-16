import json
import sys
from urllib import request

from django.apps import AppConfig
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import (PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.core.exceptions import FieldError, ObjectDoesNotExist
from django.core.mail import send_mail
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from libtekin.models import Item, Location, Mmodel
from tougshire_vistas.models import Vista
from tougshire_vistas.views import (delete_vista, get_global_vista,
                                    get_latest_vista, make_vista,
                                    retrieve_vista)

from .forms import ItemRequestForm
from .models import History, ItemRequest


def update_history(form, modelname, object, user):
    for fieldname in form.changed_data:
        try:
            old_value = str(form.initial[fieldname]),
        except KeyError:
            old_value = None

        history = History.objects.create(
            user=user,
            modelname=modelname,
            objectid=object.pk,
            fieldname=fieldname,
            old_value=old_value,
            new_value=str(form.cleaned_data[fieldname])
        )

        history.save()



class ItemRequestCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'wishlist.add_itemrequest'
    model = ItemRequest
    form_class = ItemRequestForm

    def get_initial(self):
        initial = super().get_initial()

        initial['submitted_by'] = self.request.user

        return initial


    def get_success_url(self):
        return reverse_lazy('wishlist:itemrequest-detail', kwargs={'pk': self.object.pk})


class ItemRequestUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'wishlist.change_itemrequest'

    model = ItemRequest
    form_class = ItemRequestForm

    def get_success_url(self):

        return reverse_lazy('wishlist:itemrequest-detail', kwargs={'pk': self.object.pk})

class ItemRequestDetail(PermissionRequiredMixin, DetailView):
    permission_required = 'wishlist.view_itemrequest'
    model = ItemRequest

    def get_context_data(self, **kwargs):

        context_data = super().get_context_data(**kwargs)
        context_data['itemrequest_labels'] = {field.name: field.verbose_name.title(
        ) for field in ItemRequest._meta.get_fields() if type(field).__name__[-3:] != 'Rel'}

        return context_data


class ItemRequestDelete(PermissionRequiredMixin, UpdateView):
    permission_required = 'wishlist.delete_itemrequest'
    model = ItemRequest
    success_url = reverse_lazy('wishlist:itemrequest-list')


class ItemRequestSoftDelete(PermissionRequiredMixin, UpdateView):
    permission_required = 'wishlist.delete_itemrequest'
    model = ItemRequest
    template_name = 'wishlist/item_confirm_delete.html'
    success_url = reverse_lazy('wishlist:itemrequest-list')
    fields = ['is_deleted']

    def get_context_data(self, **kwargs):

        context_data = super().get_context_data(**kwargs)
        context_data['itemrequest_labels'] = {field.name: field.verbose_name.title(
        ) for field in ItemRequest._meta.get_fields() if type(field).__name__[-3:] != 'Rel'}

        return context_data

class ItemRequestList(PermissionRequiredMixin, ListView):
    permission_required = 'wishlist.view_itemrequest'
    model = ItemRequest
    paginate_by = 30


    def setup(self, request, *args, **kwargs):

        self.vista_settings={
            'text_fields_available':[],
            'filter_fields_available':{},
            'order_by_fields_available':[],
            'columns_available':[]
        }

        self.vista_settings['text_fields_available']=[
            'description',
            'purpose',
            'notes',
            'resolution_notes',
        ]

        self.vista_settings['filter_fields_available'] = [
            'description',
            'purpose',
            'notes',
            'price',
            'link',
            'substitutability',
            'urgency',
            'status',
            'submitted_by',
            'when',
            'resolution_notes',
        ]

        for fieldname in [
            'price',
            'urgency',
            'status',
            'submitted_by',
            'when',
        ]:
            self.vista_settings['order_by_fields_available'].append(fieldname)
            self.vista_settings['order_by_fields_available'].append('-' + fieldname)

        for fieldname in [
            'description',
            'purpose',
            'notes',
            'price',
            'link',
            'substitutability',
            'urgency',
            'status',
            'submitted_by',
            'when',
            'resolution_notes',
        ]:
            self.vista_settings['columns_available'].append(fieldname)

        self.vista_defaults = {
            'order_by': Item._meta.ordering,
            'paginate_by':self.paginate_by
        }

        return super().setup(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):

        self.vista_context = {
            'show_columns':[],
            'order_by':[],
            'combined_text_search':'',
        }

        queryset = super().get_queryset()

        vistaobj={'context':{}, 'queryset':queryset}

        if 'delete_vista' in self.request.POST:
            delete_vista(self.request)

        if 'vista_query_submitted' in self.request.POST:
            vistaobj = make_vista(self.request, self.vista_settings, super().get_queryset(), self.vista_defaults)
        elif 'retrieve_vista' in self.request.POST:
            vistaobj = retrieve_vista(self.request, self.vista_settings, super().get_queryset(), self.vista_defaults)
        else:
            try:
                vistaobj =  get_latest_vista(self.request, self.vista_settings, super().get_queryset(), self.vista_defaults)
            except Exception as e:
                print(e, ' at ', sys.exc_info()[2].tb_lineno)
                try:
                    vistaobj =  get_global_vista(self.request, self.vista_settings, super().get_queryset(), self.vista_defaults)
                except Exception as e:
                    print(e, ' at ', sys.exc_info()[2].tb_lineno)

        for key in vistaobj['context']:
            self.vista_context[key] = vistaobj['context'][key]

        queryset = vistaobj['queryset']

        return queryset

    def get_paginate_by(self, queryset):

        if 'paginate_by' in self.vista_context and self.vista_context['paginate_by']:
            return self.vista_context['paginate_by']

        return super().get_paginate_by(self)

    def get_context_data(self, **kwargs):

        context_data = super().get_context_data(**kwargs)

        context_data['users'] = get_user_model().objects.all()

        context_data['order_by_fields_available'] = []
        for fieldname in self.vista_settings['order_by_fields_available']:
            if fieldname > '' and fieldname[0] == '-':
                context_data['order_by_fields_available'].append({ 'name':fieldname, 'label':ItemRequest._meta.get_field(fieldname[1:]).verbose_name.title() + ' [Reverse]'})
            else:
                context_data['order_by_fields_available'].append({ 'name':fieldname, 'label':ItemRequest._meta.get_field(fieldname).verbose_name.title()})

        context_data['columns_available'] = [{ 'name':fieldname, 'label':ItemRequest._meta.get_field(fieldname).verbose_name.title() } for fieldname in self.vista_settings['columns_available']]

        context_data['vistas'] = Vista.objects.filter(user=self.request.user, model_name='wishlist.itemrequest').all()

        if self.request.POST.get('vista__name'):
            context_data['vista__name'] = self.request.POST.get('vista__name')

        if self.vista_context:
            if 'filter' in self.vista_context:
                for key in self.vista_context['filter']:
                    context_data[key] = self.vista_context['filter'][key]

        for key in [
            'combined_text_search',
            'text_fields_chosen',
            'order_by',
            'paginate_by'
            ]:
            if key in self.vista_context and self.vista_context[key]:
                context_data[key] = self.vista_context[key]

        context_data['itemrequest_labels'] = { field.name: field.verbose_name.title() for field in ItemRequest._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }

        return context_data

    def get_success_url(self):
        return reverse_lazy('wishlist:itemrequest-detail', kwargs={'pk': self.object.itemrequest.pk})

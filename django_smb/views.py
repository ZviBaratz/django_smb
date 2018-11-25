# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django_smb.forms import RemoteLocationForm
from django_smb.models import RemoteLocation


def sync_remote_location(request, pk: int):
    smb = get_object_or_404(RemoteLocation, pk=pk)
    smb.sync()
    return redirect('smb_locations')


class RemoteLocationListView(LoginRequiredMixin, ListView):
    model = RemoteLocation
    template_name = 'django_smb/list_locations.html'


class RemoteLocationCreateView(LoginRequiredMixin, CreateView):
    form_class = RemoteLocationForm
    template_name = 'django_smb/create_location.html'
    success_url = reverse_lazy('smb_locations')

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django_smb.forms import RemoteLocationForm
from django_smb.models import RemoteLocation, RemotePath


def get_root_dicts():
    return [
        location.tree_root.to_dict()
        for location in RemoteLocation.objects.all()
    ]


def sync_remote_location(request, pk: int):
    smb = get_object_or_404(RemoteLocation, pk=pk)
    smb.sync()
    return redirect('locations')


def generate_json(request, pk: int):
    smb = get_object_or_404(RemoteLocation, pk=pk)
    data = smb.tree_root.to_dict(lazy=False)
    return JsonResponse(data)


def generate_lazy_json(request):
    pk = request.get_full_path().split('=')[-1]
    # '%23' is percent symbol for '#', which signifies a root node in jsTree
    if pk == '%23':
        data = get_root_dicts()
    else:
        node = get_object_or_404(RemotePath, pk=int(pk))
        data = [child.to_dict() for child in node.children.all()]
    return JsonResponse(data, safe=False)


class RemoteLocationListView(LoginRequiredMixin, ListView):
    model = RemoteLocation
    template_name = 'django_smb/list_locations.html'


class RemoteLocationCreateView(LoginRequiredMixin, CreateView):
    form_class = RemoteLocationForm
    template_name = 'django_smb/create_location.html'
    success_url = reverse_lazy('locations')

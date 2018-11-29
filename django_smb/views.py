# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django_smb.forms import RemoteLocationForm
from django_smb.models import RemoteLocation, RemotePath


def get_root_dicts():
    root_dicts = []
    for location in RemoteLocation.objects.all():
        if location.tree_root is None:
            location.create_tree_root()
        root_dicts.append(location.tree_root.to_dict())
    return root_dicts


def sync_ajax(request):
    if request.method == 'GET':
        request_path = request.get_full_path()
        path_id = request_path.split('=')[-1]
        node = RemotePath.objects.get(id=path_id)
        if 'lazy' in request_path:
            node.sync(lazy=True)
        else:
            node.sync()
        return HttpResponse(f'Synced node {path_id}!')
    else:
        return HttpResponse('Request method must be GET!')


def import_ajax(request):
    if request.method == 'GET':
        request_path = request.get_full_path()
        path_id = request_path.split('=')[-1]
        node = RemotePath.objects.get(id=path_id)
        if 'lazy' in request_path:
            node.sync(lazy=True)
        else:
            node.sync()
        return HttpResponse(f'Synced node {path_id}!')
    else:
        return HttpResponse('Request method must be GET!')


def sync_remote_location(request, pk: int):
    smb = get_object_or_404(RemoteLocation, pk=pk)
    smb.sync()
    return redirect('locations')


def generate_json(request, pk: int):
    smb = get_object_or_404(RemoteLocation, pk=pk)
    data = smb.tree_root.to_dict(lazy=False)
    return JsonResponse(data)


def parse_lazy_pk(request) -> int:
    value = request.get_full_path().split('=')[-1]
    try:
        return int(value)
    except ValueError:
        return 0


def generate_lazy_json(request):
    pk = parse_lazy_pk(request)
    if pk:
        node = get_object_or_404(RemotePath, pk=pk)
        data = [child.to_dict() for child in node.children.all()]
    else:
        data = get_root_dicts()
    return JsonResponse(data, safe=False)


class RemoteLocationListView(LoginRequiredMixin, ListView):
    model = RemoteLocation
    template_name = 'django_smb/list_locations.html'


class RemoteLocationCreateView(LoginRequiredMixin, CreateView):
    form_class = RemoteLocationForm
    template_name = 'django_smb/create_location.html'
    success_url = reverse_lazy('smb:locations')

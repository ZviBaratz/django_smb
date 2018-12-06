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
            result = node.sync(lazy=True)
        else:
            result = node.sync(lazy=False)
        if result:
            return HttpResponse(node.id)
        return HttpResponse('Failure')
    else:
        return HttpResponse('Request method must be GET!')


def sync_remote_location(request, pk: int):
    smb = get_object_or_404(RemoteLocation, pk=pk)
    smb.sync()
    return redirect('locations')


def parse_lazy_pk(request) -> int:
    value = request.get_full_path().split('=')[-1]
    try:
        return int(value)
    except ValueError:
        return 0


def generate_json(request):
    if request.method == 'GET':
        pk = parse_lazy_pk(request)
        if pk:
            node = get_object_or_404(RemotePath, pk=pk)
            if 'lazy' in request.get_full_path():
                data = [
                    child.to_dict(lazy=True) for child in node.children.all()
                ]
            else:
                data = node.to_dict(lazy=False)
        else:
            data = get_root_dicts()
        return JsonResponse(data, safe=False)
    else:
        return HttpResponse('Request method must be GET!')


class RemoteLocationListView(LoginRequiredMixin, ListView):
    model = RemoteLocation
    template_name = 'django_smb/list_locations.html'


class RemoteLocationCreateView(LoginRequiredMixin, CreateView):
    form_class = RemoteLocationForm
    template_name = 'django_smb/create_location.html'
    success_url = reverse_lazy('smb:locations')

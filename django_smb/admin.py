# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django_smb.models import RemoteLocation


class SMBAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'server_name',
        'share_name',
        'user_id',
    )


admin.site.register(RemoteLocation, SMBAdmin)

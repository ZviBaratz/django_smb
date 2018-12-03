import os
import socket

from datetime import datetime
from django.db import models, transaction
from django.urls import reverse
from smb.SMBConnection import SMBConnection
from django_smb.models import RemotePath


class RemoteLocation(models.Model):
    name = models.CharField(max_length=64, blank=False, unique=True)
    user_id = models.CharField(max_length=64, blank=False)
    password = models.CharField(max_length=64, blank=False)
    share_name = models.CharField(max_length=64, blank=False)
    server_name = models.CharField(max_length=64, blank=False, unique=True)
    last_sync = models.DateTimeField(null=True)

    tree_root = models.OneToOneField(
        RemotePath,
        on_delete=models.CASCADE,
        null=True,
        related_name='root_for',
    )

    class Meta:
        verbose_name_plural = "Locations"

    def get_absolute_url(self):
        return reverse('smb:locations')

    def get_server_ip(self) -> str:
        return socket.getaddrinfo(self.server_name, 139)[0][-1][0]

    def get_client_name(self) -> str:
        return socket.gethostname()

    def create_connection(self) -> SMBConnection:
        return SMBConnection(
            self.user_id,
            self.password,
            self.get_client_name(),
            self.server_name,
        )

    def connect(self) -> SMBConnection:
        conn = self.create_connection()
        ip_address = self.get_server_ip()
        # This function is called also when checking whether the directory
        # is accessible, so the timeout prevents long loading times.
        try:
            if conn.connect(ip_address, timeout=1):
                return conn
            return False
        # In case no route is found to the host
        except OSError:
            return False

    def list_files(self, path: str):
        connection = self.connect()
        if connection:
            paths = connection.listPath(self.share_name, path)[2:]
            connection.close()
            return paths

    def list_file_paths(self, path: str) -> list:
        files = self.list_files(path)
        result = []
        for f in files:
            full_path = os.path.join(path, f.filename)
            if f.isDirectory:
                result += self.list_file_paths(full_path)
            else:
                result += [full_path]
        return result

    def list_all_paths(self) -> list:
        return self.list_file_paths('.')

    def create_tree_root(self):
        new_root = RemotePath(name='.')
        new_root.save()
        self.tree_root = new_root
        self.save()

    def sync(self):
        if self.tree_root is None:
            self.create_tree_root()
        with transaction.atomic():
            with RemotePath.objects.disable_mptt_updates():
                self.tree_root.sync()
            RemotePath.objects.rebuild()
        self.last_sync = datetime.now()
        self.save()

    @property
    def is_connected(self):
        connection = self.connect()
        if connection:
            connection.close()
            return True
        return False

    def __str__(self):
        return self.name

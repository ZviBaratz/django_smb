import os
import socket

from datetime import datetime
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
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
        return reverse('smb_locations')

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

    def sync_node(self, node: RemotePath):
        current_files = self.list_files(node.relative_path)
        for shared_file in current_files:
            name = shared_file.filename
            try:
                file_node = node.children.get(name=name, parent=node)
            except ObjectDoesNotExist:
                file_node = RemotePath(name=name, parent=node)
                file_node.save()

            if shared_file.isDirectory:
                self.sync_node(file_node)

    def sync(self):
        if not self.tree_root:
            self.tree_root = RemotePath(name='.')
            self.tree_root.save()
        self.sync_node(self.tree_root)
        self.last_sync = datetime.now()
        self.save()

    # def old_sync(self):
    #     files = self.list_all_paths()
    #     for f in files:
    #         found = self.file_set.filter(path=f).first()
    #         if not found:
    #             new_file = RemoteFile(
    #                 path=f,
    #                 source=self,
    #             )
    #             new_file.save()
    #     self.last_sync = datetime.now()
    #     self.save()

    # def to_dict(self):
    #     def recurse_setdefault(res, array):
    #         if len(array) == 0:
    #             return
    #         elif len(array) == 1:
    #             res.append(array[0])
    #         else:
    #             recurse_setdefault(
    #                 res.setdefault(array[0], [] if len(array) == 2 else {}),
    #                 array[1:],
    #             )

    #     tree = {}
    #     for remote_file in self.file_set.all():
    #         recurse_setdefault(tree, remote_file.path.split('/')[1:])
    #     return tree

    @property
    def is_connected(self):
        connection = self.connect()
        if connection:
            connection.close()
            return True
        return False

    def __str__(self):
        return self.name

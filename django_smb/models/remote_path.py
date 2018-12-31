import os
import tempfile

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from treebeard.mp_tree import MP_Node
from smb.smb_structs import OperationFailure

ICON_DICT = {
    '': 'fas fa-server',
    'dcm': 'fab fa-magento',
}


class RemotePath(MP_Node):
    name = models.CharField(max_length=100, blank=False, null=False)
    created = models.DateTimeField(auto_now_add=True)
    is_imported = models.BooleanField(default=False)
    node_order_by = ['name']

    def get_absolute_url(self):
        return reverse('smb:locations')

    def to_dict(self, lazy=True) -> dict:
        d = {
            'id': str(self.id),
            'text': self.name,
        }
        if self.name is '.':
            d['text'] = self.root_for.name

        ext = self.name.split('.')[-1]
        if ext not in ICON_DICT or not ext:
            if lazy or not self.get_children():
                d['children'] = True
            else:
                d['children'] = [
                    child.to_dict(lazy=False)
                    for child in self.get_children().all()
                ]
        else:
            d['children'] = False

        d['icon'] = ICON_DICT.get(ext, 'fas fa-folder')
        if self.is_available:
            d['icon'] += ' available'
        else:
            d['icon'] += ' unavailable'
        if 'folder' not in d['icon'] and 'server' not in d['icon']:
            if self.is_imported:
                d['icon'] += ' imported'
            else:
                d['icon'] += ' notimported'
        return d

    def sync(self, lazy=False):
        location = self.get_root().root_for
        current_files = location.list_files(self.full_path)
        if current_files is not None:
            for shared_file in current_files:
                name = shared_file.filename
                try:
                    node = self.get_children().get(name=name)
                except ObjectDoesNotExist:
                    node = self.add_child(name=name)
                    node.save()
                if not lazy and shared_file.isDirectory:
                    node.sync()
            return True
        return False

    def get_file(self):
        location = self.get_root().root_for
        connection = location.connect()
        temp_file = tempfile.NamedTemporaryFile()
        connection.retrieveFile(
            location.share_name,
            self.full_path,
            temp_file,
        )
        connection.close()
        temp_file.seek(0)
        return temp_file

    @property
    def location_path(self):
        if self.is_root():
            return self.name
        return os.path.join(
            *[ancestor.name for ancestor in self.get_ancestors()])

    @property
    def full_path(self):
        if self.is_root():
            return self.name
        return os.path.join(self.location_path, self.name)

    @property
    def is_available(self):
        location = self.get_root().root_for
        try:
            dir_files = location.list_files(self.location_path)
        except (OperationFailure, AttributeError):
            return False
        if self.is_root():
            return True
        file_names = [f.filename for f in dir_files]
        if self.name in file_names:
            return True
        return False


RemotePath._meta.get_field('path').max_length = 1024

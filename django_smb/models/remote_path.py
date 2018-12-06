import os
import tempfile

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
from smb.smb_structs import OperationFailure

ICON_DICT = {
    '': 'fas fa-server',
    'dcm': 'fab fa-magento',
}


class RemotePath(MPTTModel):
    name = models.CharField(max_length=100, blank=False, null=False)
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    is_imported = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('smb:locations')

    def to_dict(self, lazy=True) -> dict:
        d = {
            'id': str(self.id),
            'text': self.name,
        }
        if self.name is '.':
            d['text'] = self.root_for.share_name

        ext = self.name.split('.')[-1]
        if ext not in ICON_DICT or not ext:
            if lazy or not self.children.exists():
                d['children'] = True
            else:
                d['children'] = [
                    child.to_dict(lazy=False) for child in self.children.all()
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
        current_files = location.list_files(self.relative_path)
        if current_files is not None:
            for shared_file in current_files:
                name = shared_file.filename
                try:
                    node = self.children.get(name=name)
                except ObjectDoesNotExist:
                    node = RemotePath(name=name, parent=self)
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
            self.relative_path,
            temp_file,
        )
        connection.close()
        temp_file.seek(0)
        return temp_file

    @property
    def relative_path(self):
        ancestors = list(
            self.get_ancestors(include_self=True).values_list(
                'name',
                flat=True,
            ))
        return str.join('/', ancestors)

    @property
    def dir_name(self):
        return os.path.dirname(self.relative_path)

    @property
    def is_available(self):
        connection = self.get_root().root_for.connect()
        try:
            dir_files = connection.listPath(
                self.get_root().root_for.share_name,
                self.dir_name,
            )
            connection.close()
        except (OperationFailure, AttributeError):
            return False
        file_names = [f.filename for f in dir_files]
        if self.name in file_names:
            return True
        return False

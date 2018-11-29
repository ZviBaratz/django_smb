import logging
import os
import tempfile

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
from smb.smb_structs import OperationFailure

logger = logging.getLogger('remote_path')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('spam.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter(
    '%(asctime)s|%(name)s|%(levelname)s|\t%(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


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

    # class MPTTMeta:
    #     order_insertion_by = ['name']

    def get_absolute_url(self):
        return reverse('smb:locations')

    def to_dict(self, lazy=True) -> dict:
        d = {'id': str(self.id), 'text': self.name}
        if self.name is '.':
            d['text'] = self.root_for.share_name
            d['icon'] = 'fas fa-server'
        if self.children.exists():
            if lazy:
                d['children'] = True
            else:
                d['children'] = [
                    child.to_dict() for child in self.children.all()
                ]
        else:
            d['children'] = False
        if self.name.endswith('.dcm'):
            d['icon'] = 'fab fa-magento'
            if self.is_available:
                d['icon'] += ' available'
            else:
                d['icon'] += ' unavailable'
            if self.is_imported:
                d['icon'] += ' imported'
            else:
                d['icon'] += ' notimported'
        return d

    def sync(self, lazy=False, log=True):

        if log:
            logger.info(f'Fetching file descriptors for {self.name}...')
        current_files = self.get_root().root_for.list_files(self.relative_path)
        if log:
            logger.info(f'{len(current_files)} files discovered.')

        for shared_file in current_files:
            name = shared_file.filename
            if log:
                logger.info(f'Looking for existing node for {name}...')
            try:
                node = self.children.get(name=name)
                if log:
                    logger.info(f'Existing node found! (ID: {node.id})')
            except ObjectDoesNotExist:
                if log:
                    logger.info(
                        f'None found! Creating new node for {name} under {self.name}...'
                    )
                node = RemotePath(name=name, parent=self)
                node.save()
                if log:
                    logger.info(f'Successfully created node #{node.id}!')

            if not lazy and shared_file.isDirectory:
                node.sync()

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

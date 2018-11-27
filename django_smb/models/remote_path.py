import logging
import os

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
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

    class MPTTMeta:
        order_insertion_by = ['name']

    def sync(self, log=True):

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
                    logger.info(f'existing node found! (ID: {node.id})')
            except ObjectDoesNotExist:
                if log:
                    logger.info('NONE!')
                    logger.info(
                        f'Creating new node for {name} under {self.name}...')
                node = RemotePath(name=name, parent=self)
                node.save()
                if log:
                    logger.info('done!')

            if shared_file.isDirectory:
                node.sync()

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
        connection = self.source.connect()
        try:
            dir_files = connection.listPath(
                self.get_root().root_for.share_name,
                self.dir_name,
            )
            connection.close()
        except OperationFailure:
            return False
        file_names = [f.filename for f in dir_files]
        if self.name in file_names:
            return True
        return False

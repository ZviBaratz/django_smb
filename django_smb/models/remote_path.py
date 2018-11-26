import os

from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from smb.smb_structs import OperationFailure


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

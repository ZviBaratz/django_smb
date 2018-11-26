import os
import tempfile

from django.db import models
from django.urls import reverse
from smb.smb_structs import OperationFailure


class RemoteFile(models.Model):
    path = models.CharField(max_length=500, blank=False)
    is_archived = models.BooleanField(default=False)
    source = models.ForeignKey(
        'django_smb.RemoteLocation',
        related_name='file_set',
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name_plural = "SMB Files"

    def get_absolute_url(self):
        return reverse('smb_files')

    def get_file(self):
        connection = self.source.connect()
        temp_file = tempfile.NamedTemporaryFile()
        connection.retrieveFile(
            self.source.share_name,
            self.path,
            temp_file,
        )
        connection.close()
        temp_file.seek(0)
        return temp_file

    def get_path_parts(self):
        return self.path.split('/')[1:]

    @property
    def dir_name(self):
        return os.path.dirname(self.path)

    @property
    def is_available(self):
        connection = self.source.connect()
        try:
            dir_files = connection.listPath(
                self.source.share_name,
                self.dir_name,
            )
            connection.close()
        except OperationFailure:
            return False
        file_names = [f.filename for f in dir_files]
        if os.path.basename(self.path) in file_names:
            return True
        return False

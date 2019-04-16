import os
import socket

from datetime import datetime
from django.db import models
from django.urls import reverse
from smb.SMBConnection import SMBConnection
from django_smb.models import RemotePath


class RemoteLocation(models.Model):
    """
    A model to represent a remote Windows Share directory.
    
    """

    name = models.CharField(
        max_length=64,
        blank=False,
        null=False,
        unique=True,
        help_text="A unique name for the remote location.",
    )
    user_id = models.CharField(
        max_length=64,
        blank=False,
        null=False,
        help_text="The name of the user that is meant to be logged in.",
    )
    password = models.CharField(
        max_length=64,
        blank=False,
        null=False,
        help_text="The password of the user that is meant to be logged in.",
    )
    share_name = models.CharField(
        max_length=64,
        blank=False,
        null=True,
        help_text="The name of the shared location.",
    )
    server_name = models.CharField(
        max_length=64,
        blank=False,
        null=False,
        help_text="The name of the server on which the shared location is found.",
    )
    last_sync = models.DateTimeField(
        blank=True, null=True, help_text="Time of the last synchronization."
    )

    # This field is meant to represent the root directory of the remote location.
    tree_root = models.OneToOneField(
        RemotePath,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="root_for",
    )

    class Meta:
        verbose_name_plural = "Locations"

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("smb:locations")

    def get_server_ip(self) -> str:
        """
        Returns the IPv4 address of the server as a string.
        
        Returns
        -------
        str
            SMB Server IPv4 address.
        """

        return socket.getaddrinfo(self.server_name, 139)[0][-1][0]

    def get_client_name(self) -> str:
        """
        Return the name of this computer (the client).
        
        Returns
        -------
        str
            Client's name.
        """

        return socket.gethostname()

    def create_connection(self) -> SMBConnection:
        """
        Uses pysmb_ to create and return a configured SMBConnection_ instance.

        .. _pysmb: https://github.com/miketeo/pysmb
        .. _SMBConnection: https://github.com/miketeo/pysmb/blob/131bc9cafa967c362a360685aa8c7086e9b26312/sphinx/source/api/smb_SMBConnection.rst
        
        Returns
        -------
        SMBConnection
            A potential connection to the remote location using SMB.
        """

        return SMBConnection(
            self.user_id, self.password, self.get_client_name(), self.server_name
        )

    def connect(self) -> SMBConnection:
        """
        Create an SMBConnection_ instance and call its connect() method with the
        remote location's server IP address.

        .. _SMBConnection: https://github.com/miketeo/pysmb/blob/131bc9cafa967c362a360685aa8c7086e9b26312/sphinx/source/api/smb_SMBConnection.rst
        
        Returns
        -------
        SMBConnection
            An active connection to the remote location using SMB.
        """

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

    def list_files(self, path: str) -> list:
        """
        Lists the files within a remote location's relative path.
        
        Parameters
        ----------
        path : str
            The relative path of the location to be listed.
        
        Returns
        -------
        list
            A list of the files and directories in the given location.
        """

        connection = self.connect()
        if connection:
            paths = connection.listPath(self.share_name, path)[2:]
            connection.close()
            return paths

    def list_files_recursively(self, path: str) -> list:
        """
        List all the files found under the remote location's specified path and
        sub-directories.
        
        Parameters
        ----------
        path : str
            The relative path of the location to be listed.
        
        Returns
        -------
        list
            All files found within the given path and its sub-directories.
        """

        files = self.list_files(path)
        result = []
        for f in files:
            full_path = os.path.join(path, f.filename)
            if f.isDirectory:
                result += self.list_files_recursively(full_path)
            else:
                result += [full_path]
        return result

    def list_all_paths(self) -> list:
        """
        List the relative paths of all the files found within the remote location
        (under its root directory).
        
        Returns
        -------
        list
            All relative file paths within the remote location.
        """

        return self.list_files_recursively(".")

    def create_tree_root(self):
        new_root = RemotePath.add_root(name=".")
        new_root.save()
        self.tree_root = new_root
        self.save()
        return self.tree_root

    def sync(self) -> None:
        """
        Synchronize the root node to update with any new remote files.
        
        """

        if self.tree_root is None:
            self.create_tree_root()
        self.tree_root.sync()
        self.last_sync = datetime.now()
        self.save()

    @property
    def is_connected(self) -> bool:
        """
        Check if a connection can be made to the remote location.
        
        Returns
        -------
        bool
            Whether the connection was successful.
        """

        connection = self.connect()
        if connection:
            connection.close()
            return True
        return False


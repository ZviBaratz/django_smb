import os
import tempfile

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from treebeard.mp_tree import MP_Node
from smb.smb_structs import OperationFailure

ICON_DICT = {"": "fas fa-server", "dcm": "fab fa-magento"}


class RemotePath(MP_Node):
    """
    A treebeard_'s `materialized path node`_ model to represent a remote path as part of a tree.
    This is meant to make the model's management easier and more efficient.
    
    .. _treebeard: https://github.com/django-treebeard/django-treebeard
    .. _materialized path node: https://django-treebeard.readthedocs.io/en/latest/mp_tree.html
    """

    name = models.CharField(
        max_length=100, blank=False, null=False, help_text="The file or directory name."
    )
    created = models.DateTimeField(
        auto_now_add=True,
        help_text="The time in which the node representing this file or directory was created.",
    )
    is_imported = models.BooleanField(
        default=False,
        help_text="Whether this file had been imported from the remote location to the client or not.",
    )
    node_order_by = ["name"]

    def get_absolute_url(self):
        return reverse("smb:locations")

    def to_dict(self, lazy: bool = True) -> dict:
        """
        Returns a dictionary meant to be used by jstree to visualize the directory
        tree. If lazy is set to True, will return only this node's dictionary,
        otherwise will run recursively and return a nested dictionary.
        
        Parameters
        ----------
        lazy : bool, optional
            Return only this node or nest children (the default is True, which will return just this node).
        
        Returns
        -------
        dict
            This node's representation as a dictionary for jstree.
        """

        d = {"id": str(self.id), "text": self.name}
        if self.name == ".":
            d["text"] = self.root_for.name

        ext = self.name.split(".")[-1]
        if ext not in ICON_DICT or not ext:
            if lazy or not self.get_children():
                d["children"] = True
            else:
                d["children"] = [
                    child.to_dict(lazy=False) for child in self.get_children().all()
                ]
        else:
            d["children"] = False

        d["icon"] = ICON_DICT.get(ext, "fas fa-folder")
        if self.is_available:
            d["icon"] += " available"
        else:
            d["icon"] += " unavailable"
        if "folder" not in d["icon"] and "server" not in d["icon"]:
            if self.is_imported:
                d["icon"] += " imported"
            else:
                d["icon"] += " notimported"
        return d

    def sync(self, lazy: bool = False) -> bool:
        """
        Checks for unfamiliar files under this node. Running in lazy mode will run
        flatly instead of recursively.
        
        Parameters
        ----------
        lazy : bool, optional
            Run lazily or recursively (the default is False, which will run recursively).
        
        Returns
        -------
        bool
            Whether the synchronization was successful or not.
        """

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

    def get_file(self) -> tempfile.NamedTemporaryFile:
        """
        Return the contents of a remote file.
        
        Returns
        -------
        tempfile.NamedTemporaryFile
            A temporary file copied from the remote location.
        """

        location = self.get_root().root_for
        connection = location.connect()
        temp_file = tempfile.NamedTemporaryFile()
        connection.retrieveFile(location.share_name, self.full_path, temp_file)
        connection.close()
        temp_file.seek(0)
        return temp_file

    @property
    def location_path(self) -> str:
        """
        Compose the relative path of this node's location using its ancestors.
        
        Returns
        -------
        str
            The relative path of this node's directory within the remote location.
        """

        if self.is_root():
            return self.name
        return os.path.join(*[ancestor.name for ancestor in self.get_ancestors()])

    @property
    def full_path(self) -> str:
        """
        Compose the full (relative) path of this node using its ancestors.
        
        Returns
        -------
        str
            This node's path within the remote location.
        """
        if self.is_root():
            return self.name
        return os.path.join(self.location_path, self.name)

    @property
    def is_available(self) -> bool:
        """
        Checks whether this node still exists within the remote location.
        
        Returns
        -------
        bool
            Node availability (existence).
        """

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

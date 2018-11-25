# django-smb



A django app to manage data sourcing from remote [SMB][1] locations.

This app creates models for SMB location configuration and file syncing.
The models are complemented with some utility methods to facilitate data import.



Quick start
-----------

1. Add "django_smb" to your INSTALLED_APPS setting like this::

<pre>
    INSTALLED_APPS = [  
        ...  
        'django_smb',  
    ]  
</pre>

2. Include the dicom URLconf in your project urls.py like this::

<pre>
    path('smb/', include('django_smb.urls')),
</pre>

3. Run `python manage.py migrate` to create the dicom models.

4. Start the development server and visit http://127.0.0.1:8000/admin/.

5. Visit http://127.0.0.1:8000/dicom/.




[1]: https://docs.microsoft.com/en-us/windows/desktop/fileio/microsoft-smb-protocol-and-cifs-protocol-overview

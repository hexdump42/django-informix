import sys

from setuptools import setup, find_packages
from distutils.core import setup, Extension

PACKAGE = 'django_informix'
VERSION = '0.1'
LICENSE = 'MIT'

setup (
    name              = PACKAGE,
    version           = VERSION,
    license           = LICENSE,
    platforms         = 'All',
    install_requires  = [ 'informixdb>=2.5',
                          'django>=1.1.0',
                          'egenix-mx-base>=3.1.2'],
    dependency_links  = [ 'http://pypi.python.org/pypi/informixdb/',
                          'http://pypi.python.org/pypi/Django/',
                          'http://pypi.python.org/pypi/egenix-mx-base'],
    description       = 'Informix support for Django framework.',
    long_description  = 'Informix support for Django framework.',
    download_url      = 'http://code.google.com/p/django-informix/downloads/list',
    author            = 'Mark Rees',
    author_email      = 'mark.john.rees@gmail.com',
    maintainer        = 'Mark Rees',
    maintainer_email  = 'mark.john.rees@gmail.com',
    url               = 'http://pypi.python.org/pypi/django-informix/',
    keywords          = 'django django_informix backends adapter Informix database db2',
    packages          = ['django_informix'],
    classifiers       = ['Development Status :: 4 - Beta',
                         'Intended Audience :: Developers',
                         'License :: OSI Approved :: MIT License',
                         'Operating System :: Microsoft :: Windows :: Windows NT/2000',
                         'Operating System :: Unix',
                         'Operating System :: POSIX :: Linux',
                         'Operating System :: MacOS',
                         'Topic :: Database :: Front-Ends'],
    data_files        = [ ('', ['./README']),
                          ('', ['./CHANGES']),
                          ('', ['./LICENSE']) ],
    zip_safe          = False,
    include_package_data = True,
)


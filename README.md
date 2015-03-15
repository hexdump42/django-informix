# Informix Database Support via Informix CSDK for Django 1.1+

In 2006, I wrote some code (http://code.google.com/p/hex-dump/source/browse/trunk/django-db-informix/) that provided informix database support for Django 0.9x. Due to changes in the Django database API, it no longer worked. This project intends to provide some code that will work with Django 1.1+.

## Dependencies

The following python packages are required to run django_informix:

    informixdb 2.5 http://informixdb.sourceforge.net/
    
    mx.DateTime? http://www.egenix.com/products/python/mxBase/mxDateTime/ 

## Limitations 

The package as yet does not pass full Django regression tests but is usable.

Textfields have a max length of 16000. Models are limited to 2 Textfields. 

Warnings similar to:

    Failed to install index for admin.LogEntry model: SQLCODE -350 in EXECUTE: 
    S0011: Index already exists

are displayed when Django attempts to re-create unique indexes on SERIAL columns during syncdb.


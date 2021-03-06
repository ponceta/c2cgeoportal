.. c2cgeoportal documentation master file, created by
   sphinx-quickstart on Mon Nov 28 10:01:14 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

c2cgeoportal documentation
==========================

Content:

.. toctree::
   :maxdepth: 1

   administrator/index
   integrator/index
   developer/index

*Administrator* is the person who manages an application built with
c2cgeoportal. *Integrator* is the person who builds the c2cgeoportal
application, and does the initial setup. *Developer* is the person who
produces code for c2cgeoportal itself.

The c2cgeoportal project is composed of two software components: NGEO (a JS
library based on `OpenLayers <https://openlayers.org>`_ and
`AngularJS <https://angularjs.org/>`_ ), and c2cgeoportal, a Python library
for the Pyramid web framework. So c2cgeoportal applications are Pyramid
applications with user interfaces based on ExtJS and
OpenLayers.

One of the primary goals of the c2cgeoportal project is sharing as much as
functionality and code as possible between applications. *Do not repeat
ourselves!*

`Demo <https://geomapfish-demo-ci.camptocamp.com/${major_version}>`_,
`with features grid <https://geomapfish-demo-ci.camptocamp.com/${major_version}/desktop_alt/>`_,
to test the editing you can use the username 'demo' with the password 'demo'.

`ngeo (client) documentation <https://camptocamp.github.io/ngeo/${major_version}/apidoc/>`_.

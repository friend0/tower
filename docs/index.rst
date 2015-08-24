.. mapServer documentation master file, created by
   sphinx-quickstart on Thu Aug 20 03:27:07 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

World Engine:
=============
For Spatially Aware Decision Making Algorithms
-----------------------------------------------

Intro
---------
World Engine uses GDAL and Rasterio to interface with raw raster data in a variety of formats.
A built-in socket server makes it possible to host this information via UDP to client applications.
The intent of this project is to offer a framework for those wishing to implement decision making algorithms on top of geographic
information.

.. image:: ../docs/img/hslLogo.png
    :align: center

Install
---------
World Engine is currently not configured or packaged for distribution. Stay tuned, as this functionality will be introduced soon.::

    pip install map_server


Motivating Examples
-------------------


.. versionadded:: version

   - Advanced API calls from Matlab/Simulink
   - Advanced request responder
   - Beta sphinx-autodoc

.. versionchanged:: version

    None

Contents:

.. toctree::
    :maxdepth: 2

    self
            world_engine
    about


.. note::

   map_server is still in beta. Suggestions, contributions, or comments are welcome.

.. warning::

   This software is still in development; as such, decision algorithms built on top of the module
   cannot be guaranteed.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Credits
=======

.. include:: ../CONTRIBUTORS.txt
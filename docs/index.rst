.. tower documentation master file, created by
   sphinx-quickstart on Tue Jul  9 22:26:36 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Tower
======================================
For Spatially Aware Decision Making Algorithms
-----------------------------------------------


Intro
---------
Tower is a Python 2/3 compatible package for developing and analyzing autonomous control algorithms for unmanned systems.
In particular, Tower was built to conduct autonomous flights of small unmanned aerial systems at the Hybrid Systems Lab at UC Santa Cruz.

Tower makes it possible to configure and execute low level control with a simple plugin API, and to interface these
controllers with real vehicles. Tower also provides a plugin architecture for higher level planning algorithms. The plugin architecture
of Tower is complemented by built-in spatial, mapping, and graph abstractions for planning paths and conducting experiments in
realistic scenarios.

Roadmap
-----------
Tower is in the early stages of development, but we have a lot planned.

.. image:: ./img/hslLogo.png
    :align: center

Install
---------
World Engine is currently not configured or packaged for distribution. Stay tuned, as this functionality will be introduced soon.::
Note: this doesn't work. Not hosting on pip yet.

    pip install map_server



Contents:

.. toctree::
   :maxdepth: 4

   self
   readme
   installation
   usage
   contributing
   authors
   history

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


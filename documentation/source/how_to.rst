How To
======

.. _how_to:

This plugin is used to run full analysis of the PSF. This analysis is composed with : 

* :ref:`Acquisition <acquisition>` phase : The user have to enter parameters of the acquisition, those will be used massively, so it is a really important step.
* :ref:`Detection <detection>` phase : The program will detect beads in image and extract region of interest by filtering beads to close from each other.
* :ref:`Metrics <metrics>` phase : It uses extracted beads to compute a gaussian fit to estimation full-width half maximum. Then calculates every metrics for analysis.
* :ref:`Outputs <results>` : It then produces many medias about analysis result to help user make his conclusions.

This section will explain the meaning and using of the widgets and parameters of the plugin.

.. toctree::
    acquisition
    detection
    metrics
    results
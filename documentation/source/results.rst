Outputs
==================

At the end of analysis, the plugin will produce many visual support to help use understand and evaluate results.

Napari viewer
-------------

The napari interface is updated to display many informations about data used and produced by analysis.
First of all, the user will see all the detected beads and extacted ROIs. Then, when metrics are computed, they are displayed in the "Metrics parameters" widget.

HTML file
---------

To make a better interaction and understanding of results, users are able to double click on a detected ROI and see a web page open with a full report concerning this bead. 
This report contains the position of the bead (coordinates and representation in image), fit curves, views from all axis, metrics found.

PDF file
--------

A PDF file containing global resultats and results for each bead is also available, it contains same informations as HTML file, but for every beads.

CSV file
--------

A CSV file only containing calculated value for each bead is also available.

.. note::
    Outputs are still under active development.





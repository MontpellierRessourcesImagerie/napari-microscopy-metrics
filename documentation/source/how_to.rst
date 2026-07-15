User Guide
==========

.. _how_to:

This plugin is designed to perform the **analysis of the Point Spread Function (PSF)**. The analysis workflow is structured into four key phases, each playing a critical role in ensuring accurate and meaningful results.

Analysis Workflow
-----------------

The plugin follows a **sequential workflow** to process PSF data:

1. :ref:`Acquisition <acquisition>`:
   The user must input the **acquisition parameters**, which are essential for the entire analysis process. These parameters are used extensively throughout the subsequent phases, making this step crucial for accurate results.

2. :ref:`Detection <detection>`:
   The program **automatically detects beads** in the image and extracts **regions of interest (ROIs)**. It filters out beads that are too close to each other to avoid overlapping or interference, ensuring that only high-quality ROIs are retained for further analysis.

3. :ref:`Metrics <metrics>`:
   Using the extracted beads, the plugin performs a **Gaussian fit** to estimate the **Full Width at Half Maximum (FWHM)**. It then calculates a comprehensive set of metrics to provide a detailed analysis of the PSF.

4. :ref:`Outputs <results>`:
   Finally, the plugin generates **various outputs**, including visualizations, reports, and other media, to help users interpret the results and draw meaningful conclusions.

---

Purpose of This Section
------------------------

This section provides a **detailed explanation** of the purpose and usage of each widget and parameter available in the plugin. It aims to guide users through the analysis process, ensuring they understand how to configure and utilize the plugin effectively.

.. toctree::
   :maxdepth: 2
   :caption: Workflow Steps

   acquisition
   detection
   metrics
   results
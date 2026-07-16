.. _getting_started:

===============
Getting started
===============

This guide will help you install and use **Napari Microscopy Metrics**, a Napari plugin for **quality control of Point Spread Functions (PSF)** in microscopy.

---

.. _installation:

Installation
------------

To use `napari microscopy metrics`, Python 3.12 is required

It is **strongly recommended** to create a Python **virtual environment** to avoid conflicts with other packages.
You can choose between **venv** (built-in Python module) or **conda** (Anaconda/Miniconda).

.. tabs::

   .. tab:: Using venv

      **1. Create a virtual environment:**

      .. code-block:: bash

         python -m venv napari_microscopy_metrics_env

      **2. Activate the virtual environment:**

      - **On Windows:**

        .. code-block:: bash

           napari_microscopy_metrics_env\Scripts\activate

      - **On macOS and Linux:**

        .. code-block:: bash

           source napari_microscopy_metrics_env/bin/activate

      **3. Install the package and its dependencies:**

      .. code-block:: bash

         #If napari is not installed yet, you can install it with pip
         pip install "napari[all]==0.6.6"

         pip install --upgrade pip
         pip install napari-microscopy-metrics

   .. tab:: Using conda

      **1. Create a conda environment:**

      .. code-block:: bash

         conda create --name napari_microscopy_metrics_env python=3.12

      **2. Activate the conda environment:**

      .. code-block:: bash

         conda activate napari_microscopy_metrics_env

      **3. Install the package:**

      .. code-block:: bash

         #If napari is not installed yet, you can install it with pip
         pip install "napari[all]==0.6.6"
         
         pip install --upgrade pip
         pip install napari-microscopy-metrics

---

.. _install_from_source:

Install from Source
--------------------

If you want to use the latest development version, you can install **Napari Microscopy Metrics** directly from the GitHub repository:

.. code-block:: bash

   git clone https://github.com/MontpellierRessourcesImagerie/napari-microscopy-metrics.git
   cd napari-microscopy-metrics
   pip install -e .

.. note::
   The ``-e`` flag installs the package in **editable mode**, allowing you to modify the code and see changes immediately.

---

.. _dependencies:

Dependencies
------------

**Napari Microscopy Metrics** relies on several Python packages for its functionality. The main dependencies include:

.. list-table:: Core Dependencies
   :header-rows: 1
   :widths: 30 70

   * - **Package**
     - **Purpose**
   * - ``numpy``
     - Numerical computations and array operations.
   * - ``scikit-image``
     - Image processing (e.g., filtering, segmentation).
   * - ``magicgui``
     - GUI creation and management.
   * - ``qtpy``
     - Qt abstraction layer for GUI compatibility.
   * - ``napari-stl-exporter``
     - Exporting 3D models to STL format.
   * - ``microscopy-metrics``
     - Core microscopy metrics calculations and analysis.

---

.. _optional_dependencies:

Optional Dependencies
---------------------

For **development and testing**, you can install the following optional dependencies:

.. code-block:: bash

   pip install napari-microscopy-metrics[dev]

This will install:

.. list-table:: Optional Dependencies
   :header-rows: 1
   :widths: 30 70

   * - **Package**
     - **Purpose**
   * - ``pytest``
     - Testing framework.
   * - ``pytest-cov``
     - Coverage reporting for tests.
   * - ``coverage``
     - Code coverage analysis.
   * - ``sphinx``
     - Documentation generation.
   * - ``sphinx-rtd-theme``
     - Theme for Sphinx documentation.
   * - ``sphinx-tabs``
     - Tab support in Sphinx documentation.

---

.. _run:

Running the Plugin
------------------

**Napari microscopy metrics** is a **Napari plugin**, so you first have to run a napari application in your python virtual environment : 

.. code-block:: bash

    napari

You now have access to the napari interface. To open the **Napari microscopy metrics** plugin, you just have to enable the option at **Plugins > Microscopy Metrics (Microscopy Metrics)**

.. image:: _static/open_plugin.png
    :width: 700px
    :alt: Open plugin example
    :align: center

A new widget is supposed to be created at the right side of the application. To use the plugin you can follow this :ref:`tutorial <how_to>` 

Contributing
------------

We welcome contributions! Here’s how you can help:

1. **Fork the repository** on GitHub.
2. **Create a new branch** for your feature or bug fix:

   .. code-block:: bash

      git checkout -b feature/your-feature-name

3. **Commit your changes**:

   .. code-block:: bash

      git commit -m "Add your feature or fix"

4. **Push to your branch**:

   .. code-block:: bash

      git push origin feature/your-feature-name

5. **Open a Pull Request** on GitHub.

For bug reports or feature requests, please open an **issue** on the `GitHub repository <https://github.com/MontpellierRessourcesImagerie/napari-microscopy-metrics/issues>`_.

---

.. _support:

Support
-------

If you encounter any issues or have questions, feel free to:

- Open an **issue** on `GitHub <https://github.com/MontpellierRessourcesImagerie/napari-microscopy-metrics/issues>`_.
- Contact the development team at **mri-cia@mri.cnrs.fr**.

---

.. _license_page:

License
-------

This project is licensed under the **CECILL-B** license. See the `LICENSE <https://cecill.info/licences/Licence_CeCILL-B_V1-fr.html>`_ file for details.

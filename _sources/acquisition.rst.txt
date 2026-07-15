.. _acquisition:

=====================
Acquisition Widget
=====================

The **Acquisition Widget** is designed to collect **essential information** about the **image scaling** and **microscope acquisition parameters**. These parameters are critical for ensuring accurate and meaningful analysis of the Point Spread Function (PSF).

---

------------------------
Image Scaling Parameters
------------------------

The **Image Scaling Parameters** section allows users to define the **physical size** represented by each pixel in the image. This scaling is specified in **µm/px** (micrometers per pixel), which means it describes the real-world distance corresponding to a single pixel in the image.

**Key Features:**
  - **Axis-Specific Scaling**: Users can enter scaling values for each axis (X, Y, Z) independently.
  - **Apply and Save**: The **"Apply and Save Scale"** button confirms the entered values for subsequent analyses and saves them for future use. It also **updates the scaling in the Napari viewer**, ensuring that the displayed image reflects the correct physical dimensions.

.. image:: _static/image_size_widget.png
    :width: 500px
    :alt: Image Scaling Widget
    :align: center
    :class: only-light

---

---------------------------------
Microscope Acquisition Parameters
---------------------------------

The **Microscope Acquisition Parameters** section allows users to specify the **technical details** of the microscope used for image acquisition. These parameters directly influence the **theoretical resolution** and the quality of the analysis.

**Parameters:**

.. list-table:: Microscope Acquisition Parameters
   :widths: 25 75
   :header-rows: 1

   * - **Parameter**
     - **Description**
   * - **Microscope Type**
     - The type of microscope used. The **theoretical resolution formula** varies depending on the microscope type. Supported types: **Widefield**, **Confocal**, **Multiphoton**, and **Spinning Disk**.
   * - **Emission Wavelength**
     - The wavelength of the photons **emitted by the sample**, measured in **nanometers (nm)**. This parameter directly impacts the resolution and image quality.
   * - **Excitation Wavelength**
     - The wavelength of the photons used to **excite the sample**, measured in **nanometers (nm)**. It influences the emission wavelength and overall imaging performance.
   * - **Refractive Index**
     - Describes how light is refracted when transitioning between different media (e.g., air, oil). Typical values range from **1.0 (air)** to **1.5 (oil)**.
   * - **Numerical Aperture (NA)**
     - Represents the **light-gathering ability** of the microscope objective. A higher NA allows more light rays to enter the objective, resulting in **higher resolution images**. It is calculated using the formula: **NA = Refractive Index × sin(θ)**, where θ is the half-angle of the cone of light that can enter the objective.

.. image:: _static/Microscope_parameters_widget.png
    :width: 500px
    :alt: Microscope Parameters Widget
    :align: center
    :class: only-light

---
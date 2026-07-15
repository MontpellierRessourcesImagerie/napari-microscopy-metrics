.. _detection:

================
Detection Widget
================

The **Detection Widget** allows users to configure parameters for **bead detection and extraction** during the analysis process.
This step is crucial for ensuring accurate and reliable results in the PSF (Point Spread Function) analysis.

--------------------
Detection Parameters
--------------------

This section allows users to select the **detection method** for identifying beads in the image.
Four detection tools are available, each with its own trade-offs between speed and accuracy:

* **Peak Local Maxima**: The fastest method, but the least accurate. Suitable for quick previews or low-noise images.
* **Laplacian of Gaussian (LoG)**: The most accurate method, but also the slowest. Ideal for high-precision analysis.
* **Difference of Gaussian (DoG)**: A faster alternative to LoG with slightly lower accuracy. A good balance between speed and precision.
* **Centroids**: Faster and more accurate than Peak Local Maxima. Recommended for most use cases.

.. image:: _static/detection_tool.png
    :width: 500px
    :alt: Detection Parameters Widget
    :align: center

--------------------
Threshold Parameters
--------------------

This interactive widget allows users to **select the threshold** for image segmentation.
To assist in this process, users can click the **"Apply"** button to preview the segmentation result in real-time.

* For **manual thresholding**, a slider is available for dynamic adjustment, with immediate visual feedback.
* Multiple thresholding algorithms are supported. By default, the **"Legacy"** method is used, as it is versatile and works well in most scenarios.
  The Legacy threshold is also used for **Signal-to-Background Ratio (SBR)** calculations.

.. note::
   For more details on thresholding methods, refer to the `microscopy-metrics <https://github.com/MontpellierRessourcesImagerie/microscopy-metrics>`_ documentation.

.. image:: _static/threshold_tool.png
    :width: 500px
    :alt: Threshold Parameters Widget
    :align: center

-----------------------------
Region of Interest Parameters
-----------------------------

This section is **critical** for bead extraction and Signal-to-Background Ratio (SBR) calculation.
Incorrect values here can significantly impact the accuracy of the analysis. Users are advised to carefully configure the following parameters: 
    
    * **Theoretical bead size (µm)** : Corresponds to the theoretical size of the bead, in other words, it is the size of the beads user wanted them to be when he made the slide.
    * **Z axis rejection margin (µm)** : When extracting ROIs, we have to pay attention to exclude beads too near to top/bottom, because they would produce a bad fit and impact the accuracy of analysis.
    * **Inner annulus distance to bead (µm)** : To compute signal to background ratio, we use a ring of pixels around the detected bead as "background". This value represents the distance between inner annulus and border of the bead.
    * **Annulus thickness (µm)** : The thickness of the ring, or the distance to inner annulus where pixels are "background".
    * **Crop factor** : The size of the ROI is estimated by : Theoretical bead size x crop factor. This crop factor is an abritrary value to make ROI bigger or smaller. Usually set to 5.
    * **Threshold mean intensity** : The intensity of a bead must be in a margin of the mean intensity of all detected beads, otherwise it is considered as a false positive and rejected. This value is a percentage of the mean intensity, usually set to 50%.
    * **Prominence relative double pass** : A peak detection is realized using a prominence value. This value is a percentage of the maximum intensity of the image, and is used to detect if two beads are in the same ROI. If the prominence of a peak is greater than this value, it is considered as a false positive and rejected.

.. image:: _static/ROI_parameters.png
    :width: 500px
    :alt: ROIParametersWidget
    :align: center
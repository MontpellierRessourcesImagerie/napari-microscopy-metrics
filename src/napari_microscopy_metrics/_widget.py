"""
This module contains a napari widgets for PSF analysis:
- A QWidget class for performing PSF detection using two methods (centroids and peak_local_max)

"""
from typing import TYPE_CHECKING, Optional
import types
from magicgui import magic_factory
from magicgui.widgets import CheckBox, Container, create_widget
from qtpy.QtCore import Qt, QSize, Signal, QObject,QThread
from qtpy.QtWidgets import *
import napari
from ._detection_tool_widget import *
from._acquisition_widget import *
from ._metrics_widget import *
from microscopy_metrics.fitting import *
from functools import partial

from reportlab.pdfgen import canvas
from reportlab.lib import colors

from matplotlib import pyplot as plt


class Worker(QObject):
    """Worker to execute analysis in a thread and send signals"""
    progress = Signal(int)
    step_progress = Signal(str)
    finished = Signal(object)
    add_layer = Signal(object,str,dict)

    def __init__(self,method,*args,**kwargs):
        super().__init__()
        self.method = method
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """ Function to link signals and start executing analysis"""
        def progress_callback(value,text):
            self.step_progress.emit(text)
            self.progress.emit(value)
        kwargs_with_callback = self.kwargs.copy()
        kwargs_with_callback['progress_callback'] = progress_callback
        result = self.method(*self.args,**kwargs_with_callback)
        self.finished.emit(result)

class Progress_widget(QWidget):
    """ Widget for displaying analysis progression
    
    Parameters
    ----------
    viewer : napari.viewer.Viewer
        The napari viewer were the widget will be displayed
    """
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.step_label = QLabel()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0,100)
        self.progress_bar.setValue(0)
        
        # Adding all the widgets to the layout
        layout.addWidget(self.step_label)
        layout.addWidget(self.progress_bar)

        # Defining the layout of the widget
        self.setLayout(layout)

class Microscopy_Metrics_QWidget(QWidget):
    """Main Widget of the Microscopy_Metrics module"""
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.parameters_detection = {
            "Min_dist":10,
            "Rel_threshold":6,
            "Sigma":3,
            "theorical_bead_size":10,
            "crop_factor":5,
            "selected_tool":0,
            "auto_threshold":False,
            "rejection_zone":10,
            "distance_annulus" : 10,
            "thickness_annulus": 10
        }
        #Read and restore datas if exist
        loaded_params = read_file_data("parameters_data.json")
        if loaded_params:
            self.parameters_detection.update(loaded_params)

        self.parameters_acquisition = {
            "PhysicSizeX":10,
            "PhysicSizeY":6,
            "PhysicSizeZ":3,
            "ShapeX":10,
            "ShapeY":5,
            "ShapeZ":0,
            "Microscope_type":"widefield",
            "Emission_Wavelength":450,
            "Refractive_index":10,
            "Numerical_aperture":1
        }
        #Read and restore datas if exist
        loaded_params = read_file_data("acquisition_data.json")
        if loaded_params:
            self.parameters_acquisition.update(loaded_params)
        
        self.filtered_layer = None
        self.filter_layer = None
        self.filtered_beads = None
        self.rois = None
        self.cropped_layers = []
        self.working_layer = None
        self.mean_SBR = 0
        self.SBR = []
        self.centroids_ROI = []
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        #TabWidget for navigation between tools
        self.tab = QTabWidget()
        self.tab.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.tab.setDocumentMode(True)

        self.acquisition_tool_page = Acquisition_tool_page(self.viewer)
        self.acquisition_tool_page.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.tab.addTab(self.acquisition_tool_page,"Acquisition parameters")
        self.detection_tool_page = Detection_Tool_Tab(self.viewer)
        self.detection_tool_page.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.tab.addTab(self.detection_tool_page,"Detection parameters")
        self.metrics_tool_page = Metrics_tool_page(self.viewer)
        self.metrics_tool_page.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.tab.addTab(self.metrics_tool_page,"Metrics parameters")

        #Button to run global analyze
        self.run_btn = QPushButton("Run")
        self.run_btn.setStyleSheet("background-color : green")
        self.run_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        
        #Creation of the layout
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setSpacing(5)

        self.layout().addWidget(self.tab)
        self.layout().addWidget(self.run_btn)

        self.run_btn.pressed.connect(self.start_processing)

    def _on_run(self,progress_callback=None):
        """Function to process analysis steps and update progress bar and label"""
        i = 0
        num_steps = 4
        if progress_callback :
            progress_callback(i, "Dectecting beads...")
        self._on_detect_psf()
        i+=1
        if progress_callback :
            progress_callback(int(i/num_steps*100), "Extracting beads...")
        self._on_crop_psf()
        i+=1
        if progress_callback :
            progress_callback(int(i/num_steps*100), "Measuring SBR...")
        self._on_SBR()
        i+=1
        if progress_callback :
            progress_callback(int(i/num_steps*100), "Compute FWHM...")
        i+=1
        if progress_callback :
            progress_callback(int(i/num_steps*100), "Finish.")


    def _on_detect_psf(self):
        """Detect and extract beads in image depending on choosen parameters"""
        self.parameters_detection = self.detection_tool_page.params
        self.parameters_acquisition = self.acquisition_tool_page.params
        
        # Extracting datas from image and user preferencies
        image = self.working_layer.data
        threshold = self.parameters_detection["Rel_threshold"]/100
        auto_threshold = self.parameters_detection["auto_threshold"]
        binary_image = None
        physical_pixel = [self.parameters_acquisition["PhysicSizeZ"],self.parameters_acquisition["PhysicSizeY"],self.parameters_acquisition["PhysicSizeX"]]
        threshold_choice = self.parameters_detection["threshold_choice"]

        # Processing bead detection using selected method by user
        if self.parameters_detection["selected_tool"] == 0 :
            show_info("Processing peak_local_max psf detection...")
            min_distance = self.parameters_detection["Min_dist"]
            self.filtered_beads = detect_psf_peak_local_max(image, min_distance, threshold,auto_threshold,threshold_choice=threshold_choice)
        elif self.parameters_detection["selected_tool"] == 1:
            show_info("Processing blob_log psf detection...")
            sigma = self.parameters_detection["Sigma"]
            self.filtered_beads = detect_psf_blob_log(image, sigma, threshold,auto_threshold,threshold_choice=threshold_choice)
        elif self.parameters_detection["selected_tool"] == 2 : 
            show_info("Processing blob_dog psf detection...")
            sigma = self.parameters_detection["Sigma"]
            self.filtered_beads = detect_psf_blob_dog(image, sigma, threshold,auto_threshold,threshold_choice=threshold_choice)
        else :
            show_info("Processing centroid psf detection...")
            self.filtered_beads,binary_image = detect_psf_centroid(image,threshold, auto_threshold,threshold_choice=threshold_choice)
        
        # Extracting region of interest from identified beads
        if isinstance(self.filtered_beads, np.ndarray) and self.filtered_beads.size > 0 :
            self.rois,self.centroids_ROI = extract_Region_Of_Interest(image,self.filtered_beads,bead_size=self.parameters_detection["theorical_bead_size"],crop_factor=self.parameters_detection["crop_factor"], rejection_zone=self.parameters_detection["rejection_zone"], physical_pixel=physical_pixel)
        
    def _on_crop_psf(self):
        """Crop the image along ROIs and generate a new layer for each"""
        self.cropped_layers = []
        for i,roi in enumerate(self.rois):
            data = self.working_layer.data[...,roi[0][1]:roi[2][1],roi[0][2]:roi[1][2]]
            self.cropped_layers.append(data)

    def _on_SBR(self):
        """Measure de mean signal to background ratio of ROIs in the image"""
        physical_pixel = [self.parameters_acquisition["PhysicSizeZ"],self.parameters_acquisition["PhysicSizeY"],self.parameters_acquisition["PhysicSizeX"]]
        self.mean_SBR,self.SBR = signal_to_background_ratio_annulus(self.cropped_layers,self.parameters_detection["distance_annulus"],self.parameters_detection["thickness_annulus"],physical_pixel)
        self.metrics_tool_page.print_results(self.mean_SBR)
        mean_SBR,SBR = signal_to_background_ratio(self.cropped_layers)
        print(mean_SBR,SBR)

    def display_layers(self):
        """Add layers for detected beads and extracted ROIs"""
        active_layer = self.viewer.layers.selection.active
        if isinstance(self.filtered_beads, np.ndarray) and self.filtered_beads.size > 0 :
            if self.filtered_layer is None :
                self.filtered_layer = self.viewer.add_points(self.filtered_beads,name="PSF detected", face_color='red', opacity=0.5, size=2)
            else : 
                self.filtered_layer.data = self.filtered_beads
            self.detection_tool_page.results_label.setText(f"Here are the results of the detection :\n- {len(self.filtered_beads)} bead(s) detected\n- {len(self.rois)} ROI(s) extracted")
        else :
            show_warning("No PSF found or incorrect format.")
        if len(self.rois) > 0:
            if self.filter_layer is None :
                self.filter_layer = self.viewer.add_shapes(self.rois,shape_type="rectangle",name="ROI",edge_color="blue",face_color="transparent")
            else :
                self.viewer.layers.remove(self.filter_layer)
                self.filter_layer = self.viewer.add_shapes(self.rois,shape_type="rectangle",name="ROI",edge_color="blue",face_color="transparent")
        self.viewer.layers.selection.active = active_layer

    def start_processing(self):
        """Initialize thread for analysis and create the progress bar window"""
        self.working_layer = self.viewer.layers.selection.active
        if self.working_layer is None or not isinstance(self.working_layer, napari.layers.Image) : # Catch if Image layer not selected
            show_error("Please, select a valid layer of type Image")
            return 
        self.detection_tool_page.erase_Layers()
        self.run_btn.setEnabled(False)
        
        self.Progress_window = QDialog(self)
        self.Progress_window.setWindowTitle("Processing analysis...")
        self.Progress_window.setModal(True)
        progress_widget = Progress_widget(self.viewer)
        progress_layout = QVBoxLayout()
        progress_layout.addWidget(progress_widget)
        self.Progress_window.setLayout(progress_layout)
        self.Progress_window.show()

        self.thread = QThread()
        worker_method = partial(self._on_run)
        self.worker = Worker(worker_method)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(progress_widget.progress_bar.setValue)
        self.worker.step_progress.connect(progress_widget.step_label.setText)
        self.worker.finished.connect(self.on_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_finished(self,result):
        """Called when the analysis is over to update states of the application"""
        self.run_btn.setEnabled(True)
        self.display_layers()
        self.compute_fwhm()
        self.generate_pdf_report()
        self.Progress_window.close()

    def compute_fwhm(self):
        image = self.cropped_layers[0]
        image_float = image.astype(np.float32)
        image_float = (image_float - np.min(image_float)) / (np.max(image_float) - np.min(image_float) + 1e-6)
        image_float[image_float < 0] = 0
        print("Dimensions de l'image :", image_float.shape)
        spacing_x = self.parameters_acquisition["PhysicSizeX"]
        centroid_idx = self.centroids_ROI[0]
        z_physic = int(self.filtered_beads[centroid_idx][0])
        y_physic = int(self.filtered_beads[centroid_idx][1] - self.rois[0][0][1])
        print(z_physic,y_physic)
        psf_x = image_float[z_physic, y_physic, :]
        coords_x = np.arange(len(psf_x))
        y_lim = [0,psf_x.max() * 1.1]
        bg = np.median(psf_x[psf_x < np.percentile(psf_x,25)])
        amp = psf_x.max() - bg
        sigma = np.sqrt(get_cov_matrix(np.clip(psf_x - bg, 0, psf_x.max()), [spacing_x], (self.filtered_beads[self.centroids_ROI[0]] - self.rois[0][0])))
        mu = self.filtered_beads[centroid_idx][2] * spacing_x
        fit_curve_1D(amp,bg,mu,sigma,coords_x,psf_x,y_lim)


    def generate_pdf_report(self):
        """First version of a pdf generator to save analysis results on a pdf file"""
        active_layer = self.viewer.layers.selection.active
        output_dir = os.path.expanduser("~/")
        default_path = os.path.expanduser("~/PSF_analysis_result.pdf")
        if active_layer is not None and hasattr(active_layer,'source') and active_layer.source.path :
            image_path = active_layer.source.path
            output_dir = os.path.dirname(image_path)
            output_path = os.path.join(output_dir,"PSF_analysis_result.pdf")
        else :
            output_path = default_path            
        pdf = canvas.Canvas(output_path)
        pdf.setTitle("PSF analysis results")
        pdf.setFont("Helvetica-Bold", 36)
        pdf.drawCentredString(300,770, 'Results')
        pdf.line(30,710,550,710)
        textLines = [
            f"Identified beads : {len(self.filtered_beads)}",
            f"Extracted ROIs : {len(self.rois)}",
            f"Signal to background ratio : {self.mean_SBR:.2f}"
        ]
        text = pdf.beginText(40,680)
        text.setFont("Courier", 18)
        for line in textLines :
            text.textLine(line)
        pdf.drawText(text)
        pdf.save()
        for i,psf in enumerate(self.cropped_layers):
            active_path = os.path.join(output_dir,f"bead_{i}")
            if not os.path.exists(active_path):
                os.makedirs(active_path)
            active_path = os.path.join(active_path,"PSF_analysis_result.pdf")
            pdf_bead = canvas.Canvas(active_path)
            pdf_bead.setTitle(f"Bead {i} results")
            pdf_bead.setFont("Helvetica-Bold", 36)
            pdf_bead.drawCentredString(300,770, 'Results')
            pdf_bead.line(30,710,550,710)
            textLines = [
                f"centroid : {self.filtered_beads[self.centroids_ROI[i]]}",
                f"Signal to background ratio : {self.SBR[i]:.2f}"
            ]
            text = pdf_bead.beginText(40,680)
            text.setFont("Courier", 18)
            for line in textLines :
                text.textLine(line)
            pdf_bead.drawText(text)
            pdf_bead.save()


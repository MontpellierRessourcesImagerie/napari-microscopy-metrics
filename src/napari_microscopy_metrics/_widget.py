"""
This module contains a napari widgets for PSF analysis:
- A QWidget class for performing PSF detection using two methods (centroids and peak_local_max)

"""
from typing import TYPE_CHECKING, Optional
import types
import napari
from napari.qt.threading import thread_worker
from napari.utils import progress
from magicgui import magic_factory
from magicgui.widgets import CheckBox, Container, create_widget
from qtpy.QtCore import Qt, QSize, Signal, QObject,QThread
from qtpy.QtWidgets import *
from ._detection_tool_widget import *
from._acquisition_widget import *
from ._metrics_widget import *
from microscopy_metrics.fitting import *
from microscopy_metrics.report_generator import *
import webbrowser


class Microscopy_Metrics_QWidget(QWidget):
    """Main Widget of the Microscopy_Metrics module

    Args:
        QWidget: Parent widget of the plugin
    """
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.analysis_data = []
        self.DetectionTool = Detection()
        self.MetricTool = Metrics()
        self.FittingTool = Fitting()
        self.report_generator = Report_Generator()
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
            "Refractive_index":0.9,
            "Numerical_aperture":1
        }
        # Read and restore datas if exist
        loaded_params = read_file_data("acquisition_data.json")
        if loaded_params:
            self.parameters_acquisition.update(loaded_params)
        # Declaration of the layers
        self.centroids_layer = None
        self.rois_layer = None
        # List of all detected bead centroid
        self.filtered_beads = None
        # Layer containing the Image to analyse
        self.working_layer = None
        # Output directory based on current Image
        self.output_dir = None
        # Metrics of the picture
        self.mean_SBR = 0
        # Actual shape selected
        self.selected_shape = 0
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # TabWidget for navigation between tools
        self.tab = QTabWidget()
        self.tab.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.tab.setDocumentMode(True)
        # Initialisation of Acquisition tool page
        self.acquisition_tool_page = Acquisition_tool_page(self.viewer)
        self.acquisition_tool_page.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.tab.addTab(self.acquisition_tool_page,"Acquisition parameters")
        # Initialisation of Detection tool page
        self.detection_tool_page = Detection_Tool_Tab(self.viewer)
        self.detection_tool_page.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.tab.addTab(self.detection_tool_page,"Detection parameters")
        # Initialisation of Metrics tool page
        self.metrics_tool_page = Metrics_tool_page(self.viewer)
        self.metrics_tool_page.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.tab.addTab(self.metrics_tool_page,"Metrics parameters")
        #Button to run global analyze
        self.run_btn = QPushButton("Run analysis")
        self.run_btn.setStyleSheet("background-color : green")
        self.run_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        #Creation of the layout
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setSpacing(5)
        self.layout().addWidget(self.tab)
        self.layout().addWidget(self.run_btn)
        # Connect signals and slots
        self.run_btn.pressed.connect(self.start_processing)
        self.viewer.mouse_double_click_callbacks.append(self._on_mouse_double_click)


    def start_processing(self):
        """Initialize layers and start thread for analysis"""
        self.working_layer = self.viewer.layers.selection.active
        self.analysis_data = []
        if self.working_layer is None or not isinstance(self.working_layer, napari.layers.Image) : # Catch if Image layer not selected
            show_error("Please, select a valid layer of type Image")
            return 
        self.detection_tool_page.erase_Layers()
        self.run_btn.setEnabled(False)
        self.apply_detect_psf()


    def apply_detect_psf(self):
        """Update DetectionTool with new values and start a new worker for detection"""
        self.parameters_detection = self.detection_tool_page.params
        self.parameters_acquisition = self.acquisition_tool_page.params
        image = self.working_layer.data
        threshold = self.parameters_detection["Rel_threshold"]/100
        auto_threshold = self.parameters_detection["auto_threshold"]
        threshold_choice = self.parameters_detection["threshold_choice"]
        self.DetectionTool.image = image
        self.DetectionTool.threshold_rel = threshold
        if auto_threshold : 
            self.DetectionTool.threshold_choice = threshold_choice
        self.DetectionTool.min_distance = self.parameters_detection["Min_dist"]
        self.DetectionTool.sigma = self.parameters_detection["Sigma"]
        self.DetectionTool.crop_factor = self.parameters_detection["crop_factor"]
        self.DetectionTool.bead_size = self.parameters_detection["theorical_bead_size"]
        self.DetectionTool.rejection_distance = self.parameters_detection["rejection_zone"]
        self.DetectionTool.pixel_size = np.array([self.parameters_acquisition["PhysicSizeZ"],self.parameters_acquisition["PhysicSizeY"],self.parameters_acquisition["PhysicSizeX"]])
        self.output_dir = os.path.expanduser("~/")
        if self.working_layer is not None and hasattr(self.working_layer,'source') and self.working_layer.source.path :
            image_path = self.working_layer.source.path
            self.output_dir = os.path.dirname(image_path)
        args = [self.parameters_detection["selected_tool"],self.output_dir]
        worker = create_worker(self.DetectionTool.run,
                                *args,
                                _progress={'desc':'Detecting beads...'}
                            )
        worker.finished.connect(self.detect_finished)
        worker.errored.connect(self.on_report_finished)
        worker.yielded.connect(lambda value: worker.pbar.set_description(value['desc']))
        worker.start()


    def detect_finished(self):
        """Function to update napari with new layers displaying bead detection

        Raises:
            ValueError: Error raised when the bead detection did not worked or if there are no beads in the image
        """
        self.filtered_beads = self.DetectionTool.centroids
        if isinstance(self.filtered_beads, np.ndarray) and self.filtered_beads.size > 0 :
            rois = self.DetectionTool.rois_extracted
            centroids_ROI = self.DetectionTool.list_id_centroids_retained
            for x,id in enumerate(centroids_ROI) :
                data = {"id":id,"ROI":rois[x]}
                self.analysis_data.append(data)
        if len(self.DetectionTool.cropped) == 0 :
            raise ValueError("There are no cropped PSF !")
        for i in range(len(self.DetectionTool.cropped)):
            self.analysis_data[i]["cropped"] = self.DetectionTool.cropped[i]
        self.display_layers()
        self.apply_prefitting_metrics()


    def apply_prefitting_metrics(self):
        """Function to update MetricTool and start a worker for prefitting metrics calculation"""
        physical_pixel = [self.parameters_acquisition["PhysicSizeZ"],self.parameters_acquisition["PhysicSizeY"],self.parameters_acquisition["PhysicSizeX"]]
        self.MetricTool.image = self.working_layer.data
        self.MetricTool.images = [entry["cropped"] for entry in self.analysis_data]
        self.MetricTool.ring_inner_distance = self.parameters_detection["distance_annulus"]
        self.MetricTool.ring_thickness = self.parameters_detection["thickness_annulus"]
        self.MetricTool.pixel_size = np.array(physical_pixel)
        worker = create_worker(self.MetricTool.run_prefitting_metrics,
                                _progress={'desc':'Metrics calculation...'}
                            )
        worker.finished.connect(self.prefitting_finished)
        worker.errored.connect(self.on_report_finished)
        worker.start()


    def prefitting_finished(self):
        """Function to update napari display with prefitting metrics results

        Raises:
            ValueError: Raised when an error occured in the signal to bakground ratio computation
        """
        if len(self.MetricTool.SBR) != len(self.analysis_data) :
            raise ValueError('Problem with SBR calculation')
        for x,sbr in enumerate(self.MetricTool.SBR) :
            self.analysis_data[x]["SBR"] = sbr
        self.metrics_tool_page.print_results(self.MetricTool.mean_SBR)
        self.mean_SBR = self.MetricTool.mean_SBR
        self.apply_fitting()


    def apply_fitting(self):
        """Function to update FittingTool and start a worker for Gaussian fitting"""
        self.FittingTool.images = [entry["cropped"] for entry in self.analysis_data]
        centroids_idx = [entry["id"] for entry in self.analysis_data]
        self.FittingTool.centroids = [self.filtered_beads[i] for i in centroids_idx]
        self.FittingTool.spacing = [self.parameters_acquisition["PhysicSizeZ"],self.parameters_acquisition["PhysicSizeY"],self.parameters_acquisition["PhysicSizeX"]]
        self.FittingTool.rois = [entry["ROI"] for entry in self.analysis_data]
        self.FittingTool.output_dir = self.output_dir

        worker = create_worker(self.FittingTool.compute_fitting_1D,
                                _progress={'desc':'Gaussian fitting...'}
                            )
        worker.finished.connect(self.on_finished)
        worker.errored.connect(self.on_report_finished)
        worker.start()


    def on_finished(self):
        """Function to update result collection and start a worker for report generation"""
        for i,result in enumerate(self.FittingTool.results):
            self.analysis_data[result[0]]["FWHM"] = []
            self.analysis_data[result[0]]["uncertainty"] = []
            self.analysis_data[result[0]]["determination"] = []
            self.analysis_data[result[0]]["FWHM"] = result[1]
            self.MetricTool.FWHM = result[1]
            self.MetricTool.lateral_asymmetry_ratio()
            self.analysis_data[result[0]]["LAR"] = self.MetricTool.LAR
            self.MetricTool.sphericity()
            self.analysis_data[result[0]]["sphericity"] = self.MetricTool.spherict
            self.analysis_data[result[0]]["uncertainty"] = result[2]
            self.analysis_data[result[0]]["determination"] = result[3]
        worker = create_worker(self.generate_report,
                            _progress={'desc':"Generating report..."}
                            )
        worker.finished.connect(self.on_report_finished)
        worker.errored.connect(self.on_report_finished)
        worker.yielded.connect(lambda value: worker.pbar.set_description(value['desc']))
        worker.start()
 

    def generate_report(self):
        """Function for generating pdf,csv and html reports

        Yields:
            string : used to change the description of the napari progress bar
        """
        # Extracting ROIs and cropped layers from analysis_data
        rois = [entry["ROI"] for entry in self.analysis_data]
        cropped_layers = [entry["cropped"] for entry in self.analysis_data]
        output_dir = os.path.expanduser("~/")
        default_path = os.path.expanduser("~/PSF_analysis_result.pdf")
        image_path = output_dir
        if self.working_layer is not None and hasattr(self.working_layer,'source') and self.working_layer.source.path :
            image_path = self.working_layer.source.path
            output_dir = os.path.dirname(image_path)
            output_path = os.path.join(output_dir,f"{self.working_layer.name}_analysis_result.pdf")
            output_csv_path = os.path.join(output_dir,f"{self.working_layer.name}_analysis_result.csv")
        else :
            output_path = default_path    
        self.report_generator.output_dir = output_dir
        self.report_generator.output_path = output_path
        self.report_generator.analysis_data = self.analysis_data
        self.report_generator.parameters_acquisition = self.parameters_acquisition
        self.report_generator.parameters_detection = self.parameters_detection
        self.report_generator.filtered_beads = self.filtered_beads
        self.report_generator.mean_SBR = self.mean_SBR
        yield {'desc' : "Generating pdf..."}
        self.report_generator.generate_pdf_report(image_path)
        yield {'desc' : "Generating html..."}
        self.report_generator.generate_html_report()
        yield {'desc' : "Generating csv..."}
        self.report_generator.generate_csv_report(output_csv_path)
    
    
    def on_report_finished(self):
        self.run_btn.setEnabled(True)

    def _open_browser(self):
        active_path = self.get_active_path(index=self.selected_shape)
        active_path = os.path.join(active_path,"PSF_analysis_result.html")
        webbrowser.open(active_path)


    def _on_mouse_double_click(self,layer,event):
        """Function to display html report corresponding to the bead selected by user.

        Args:
            layer : Information about the layer clicked sent with the signal
            event : Informations relative to the event sent with the signal
        """
        
        click_pos = self.viewer.cursor.position / self.working_layer.scale

        if self.rois_layer is None :
            return

        for i,shape in enumerate(self.rois_layer.data):
            y_coords = [point[1] for point in shape]
            x_coords = [point[2] for point in shape]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            if click_pos[1] >= y_min and click_pos[1] <= y_max and click_pos[2] >= x_min and click_pos[2] <= x_max:
                self.selected_shape = i
                self._open_browser()
                event.handled = True
                return
        

    def get_active_path(self, index):
        """
        Args:
            index (int): Bead ID corresping to it's position in the list

        Returns:
            Path: Folder's path found (or created) for the selected bead 
        """
        active_path = os.path.join(self.output_dir,f"bead_{index}")
        if not os.path.exists(active_path):
            os.makedirs(active_path)
        return active_path


    def display_layers(self):
        """Add layers for detected beads and extracted ROIs
        Update scale and units of the napari viewer"""
        rois = [entry["ROI"] for entry in self.analysis_data]
        if isinstance(self.filtered_beads, np.ndarray) and self.filtered_beads.size > 0 :
            if self.centroids_layer is None :
                self.centroids_layer = self.viewer.add_points(self.filtered_beads,name="PSF detected", face_color='red', opacity=0.5, size=2)
            else : 
                self.centroids_layer.data = self.filtered_beads
            self.detection_tool_page.results_label.setText(f"Here are the results of the detection:\n- {len(self.filtered_beads)} bead(s) detected\n- {len(rois)} ROI(s) extracted")
        else :
            show_warning("No PSF found or incorrect format.")
        if len(rois) > 0:
            features ={'label' : [f"bead_{i}" for i in range(len(rois))]} 
            text = {'string': '{label}','anchor': 'upper_left','translation': [5, -5,5],'size': 8,'color': 'green'}
            if self.rois_layer is None :
                self.rois_layer = self.viewer.add_shapes(rois,features=features,text=text,shape_type="rectangle",name="ROI",edge_color="blue",face_color="transparent")
            else :
                self.viewer.layers.remove(self.rois_layer)
                self.rois_layer = None
                self.rois_layer = self.viewer.add_shapes(rois,features=features,text=text,shape_type="rectangle",name="ROI",edge_color="blue",face_color="transparent")
        self.viewer.layers.selection.active = self.working_layer
        for i in range(len(self.viewer.layers)):
            self.viewer.layers[i].units = "µm"
            self.viewer.layers[i].scale = self.DetectionTool.pixel_size

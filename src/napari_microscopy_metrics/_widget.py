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
from functools import partial
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle,getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from jinja2 import Environment, FileSystemLoader
import webbrowser
from PIL import Image
from concurrent.futures import ThreadPoolExecutor,as_completed
from skimage.draw import polygon_perimeter



class Microscopy_Metrics_QWidget(QWidget):
    """Main Widget of the Microscopy_Metrics module"""
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.analysis_data = []
        self.DetectionTool = Detection()
        self.MetricTool = Metrics()
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


    @thread_worker(progress={'total': 2, 'desc' : 'Process analysis'})
    def _on_run(self):
        """Function to process analysis steps and update progress bar and label"""
        try:
            # Computation of Full Width at Half Maximum
            yield {'progress' : 0,'desc':'Computing FWHM'}
            self.compute_fwhm()

            yield {'progress' : 1, 'desc' : 'Finish.'}
        except Exception as e:
            print(f"Error during analysis: {e}")
            self.filtered_beads = np.zeros((0, 3))
            raise

    def apply_detect_psf(self):
        self.parameters_detection = self.detection_tool_page.params
        self.parameters_acquisition = self.acquisition_tool_page.params
        # Extracting datas from image and user preferencies
        image = self.working_layer.data
        threshold = self.parameters_detection["Rel_threshold"]/100
        auto_threshold = self.parameters_detection["auto_threshold"]
        physical_pixel = [self.parameters_acquisition["PhysicSizeZ"],self.parameters_acquisition["PhysicSizeY"],self.parameters_acquisition["PhysicSizeX"]]
        threshold_choice = self.parameters_detection["threshold_choice"]
        self.DetectionTool.set_image(image)
        self.DetectionTool.threshold_rel = threshold
        if auto_threshold : 
            self.DetectionTool.threshold_choice = threshold_choice
        self.DetectionTool.min_distance = self.parameters_detection["Min_dist"]
        self.DetectionTool.sigma = self.parameters_detection["Sigma"]
        self.DetectionTool.crop_factor = self.parameters_detection["crop_factor"]
        self.DetectionTool.bead_size = self.parameters_detection["theorical_bead_size"]
        self.DetectionTool.rejection_distance = self.parameters_detection["rejection_zone"]
        self.DetectionTool.pixel_size = np.array(physical_pixel)
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
        worker.yielded.connect(lambda value: worker.pbar.set_description(value['desc']))
        worker.start()


    def detect_finished(self):
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


    def get_active_path(self, index):
        """Utility function to return the current path of a given bead"""
        active_path = os.path.join(self.output_dir,f"bead_{index}")
        if not os.path.exists(active_path):
            os.makedirs(active_path)
        return active_path


    def apply_prefitting_metrics(self):
        physical_pixel = [self.parameters_acquisition["PhysicSizeZ"],self.parameters_acquisition["PhysicSizeY"],self.parameters_acquisition["PhysicSizeX"]]
        self.MetricTool.image = self.working_layer.data
        self.MetricTool.images = [entry["cropped"] for entry in self.analysis_data]
        self.MetricTool.ring_inner_distance = self.parameters_detection["distance_annulus"]
        self.MetricTool.ring_thickness = self.parameters_detection["thickness_annulus"]
        self.MetricTool.pixel_size = np.array(physical_pixel)
        worker = create_worker(self.MetricTool.run_prefitting_metrics,
                                _progress={'desc':'Detecting beads...'}
                            )
        worker.finished.connect(self.prefitting_finished)
        worker.yielded.connect(lambda value: worker.pbar.set_description(value['desc']))
        worker.errored.connect(self.detect_finished)
        worker.start()


    def prefitting_finished(self):
        if len(self.MetricTool.SBR) != len(self.analysis_data) :
            raise ValueError('Problem with SBR calculation')
        for x,sbr in enumerate(self.MetricTool.SBR) :
            self.analysis_data[x]["SBR"] = sbr
        self.metrics_tool_page.print_results(self.MetricTool.mean_SBR)
        self.worker = self._on_run()
        self.worker.yielded.connect(self._update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()


    def _on_SBR(self):
        """Measure de mean signal to background ratio of ROIs in the image"""
        physical_pixel = [self.parameters_acquisition["PhysicSizeZ"],self.parameters_acquisition["PhysicSizeY"],self.parameters_acquisition["PhysicSizeX"]]
        cropped_layers = [entry["cropped"] for entry in self.analysis_data]
        # Calculation of signal to backgrounf ratio (using annulus method)
        self.mean_SBR,SBR = signal_to_background_ratio_annulus(cropped_layers,self.parameters_detection["distance_annulus"],self.parameters_detection["thickness_annulus"],physical_pixel)
        # For each bead, save the result
        if len(SBR) != len(self.analysis_data) :
            raise ValueError('Problem with SBR calculation')
        for x,sbr in enumerate(SBR) :
            self.analysis_data[x]["SBR"] = sbr
        # Display mean result in the application
        self.metrics_tool_page.print_results(self.mean_SBR)


    def display_layers(self):
        """Add layers for detected beads and extracted ROIs"""
        # Collecing every rois from analysis_data
        rois = [entry["ROI"] for entry in self.analysis_data]
        # Creation of the filtered_beads layer to display every detected centroid by a little red point
        if isinstance(self.filtered_beads, np.ndarray) and self.filtered_beads.size > 0 :
            if self.centroids_layer is None :
                self.centroids_layer = self.viewer.add_points(self.filtered_beads,name="PSF detected", face_color='red', opacity=0.5, size=2)
            else : 
                self.centroids_layer.data = self.filtered_beads
            self.detection_tool_page.results_label.setText(f"Here are the results of the detection:\n- {len(self.filtered_beads)} bead(s) detected\n- {len(rois)} ROI(s) extracted")
        else :
            show_warning("No PSF found or incorrect format.")
        # Creation of the rois layer to display every extracted ROIs
        if len(rois) > 0:
            # Defining a text for each ROI to name them
            features ={'label' : [f"bead_{i}" for i in range(len(rois))]} 
            text = {'string': '{label}','anchor': 'upper_left','translation': [5, -5,5],'size': 8,'color': 'green'}
            if self.rois_layer is None :
                self.rois_layer = self.viewer.add_shapes(rois,features=features,text=text,shape_type="rectangle",name="ROI",edge_color="blue",face_color="transparent")
            else :
                self.viewer.layers.remove(self.rois_layer)
                self.rois_layer = self.viewer.add_shapes(rois,features=features,text=text,shape_type="rectangle",name="ROI",edge_color="blue",face_color="transparent")
        self.viewer.layers.selection.active = self.working_layer


    def start_processing(self):
        """Initialize thread for analysis and create the progress bar window"""
        self.working_layer = self.viewer.layers.selection.active
        self.analysis_data = []
        if self.working_layer is None or not isinstance(self.working_layer, napari.layers.Image) : # Catch if Image layer not selected
            show_error("Please, select a valid layer of type Image")
            return 
        self.detection_tool_page.erase_Layers()
        self.run_btn.setEnabled(False)
        self.apply_detect_psf()


    def _update_progress(self,result):
        self.worker.pbar.set_description(result["desc"])


    def on_finished(self):
        """Called when the analysis is over to update states of the application"""
        self.run_btn.setEnabled(True)
        self.generate_pdf_report()


    def compute_fwhm(self):
        """Process 1D Gaussian fitting on a profile of each dimension to compute Full width at half maximum for each axis"""
        # Extracting ROIs and cropped layers from analysis_data
        rois = [entry["ROI"] for entry in self.analysis_data]
        cropped_layers = [entry["cropped"] for entry in self.analysis_data]
        def process_single_fit(i,rois,cropped_layers):
            result = [i]
            for _ in range(3) :
                result.append([])
            # Cropped picture extraction
            image = cropped_layers[i]
            image_float = image.astype(np.float64)
            image_float = (image_float - np.min(image_float)) / (np.max(image_float) - np.min(image_float) + 1e-6)
            image_float[image_float < 0] = 0
            # Initialising global variables of the picture
            active_path = self.get_active_path(index=i)
            spacing = [self.parameters_acquisition["PhysicSizeZ"],self.parameters_acquisition["PhysicSizeY"],self.parameters_acquisition["PhysicSizeX"]]
            centroid_idx = self.analysis_data[i]["id"]
            physic = [int(self.filtered_beads[centroid_idx][0]), int(self.filtered_beads[centroid_idx][1] - rois[i][0][1]), int(self.filtered_beads[centroid_idx][2] - rois[i][0][2])]
            psf = [image_float[:,physic[1],physic[2]],image_float[physic[0],:,physic[2]],image_float[physic[0],physic[1],:]]
            axe = ["Z","Y","X"]
            coords = [np.arange(len(psf[0])),np.arange(len(psf[1])),np.arange(len(psf[2]))]
            # Gaussian fit for each axis
            for u in range(3):
                lim = [0,psf[u].max() * 1.1]
                bg = np.median(psf[u])
                amp = psf[u].max() - bg
                sigma = np.sqrt(get_cov_matrix(np.clip(psf[u] - bg, 0, psf[u].max()), [spacing[u]], (self.filtered_beads[centroid_idx] - rois[i][0])))
                mu = np.argmax(psf[u])
                params,pcov = fit_curve_1D(amp,bg,mu,sigma,coords[u],psf[u],lim)
                with plt.ioff():
                    fig = plt.figure(figsize=(15, 5))
                    ax2 = fig.add_subplot(1, 2, 2)
                    plot_fit_1d(psf[u], coords[u], params, "Fit", lim, ax=ax2)
                    output_path = os.path.join(active_path, f'fit_curve_1D_{axe[u]}.png')
                    fig.savefig(output_path, dpi=300, bbox_inches='tight')
                    plt.close(fig)

                result[1].append(fwhm(params[3]))
                result[2].append(uncertainty(pcov))
                result[3].append(determination(params,coords[u],psf[u]))
            return result
        
        with ThreadPoolExecutor() as executor :
            futures = {executor.submit(process_single_fit,i,rois,cropped_layers) : i for i, roi in enumerate(rois)}

            for future in as_completed(futures):
                try :
                    result = future.result()
                    self.analysis_data[result[0]]["FWHM"] = []
                    self.analysis_data[result[0]]["uncertainty"] = []
                    self.analysis_data[result[0]]["determination"] = []
                    self.analysis_data[result[0]]["FWHM"] = result[1]
                    self.analysis_data[result[0]]["uncertainty"] = result[2]
                    self.analysis_data[result[0]]["determination"] = result[3]
                except Exception as e :
                    print(f"Fail : {e}")
 

    def compute_fwhm_2D(self):
        """Process 1D Gaussian fitting on a profile of each dimension to compute Full width at half maximum for each axis"""
        active_layer = self.viewer.layers.selection.active
        output_dir = os.path.expanduser("~/")
        if active_layer is not None and hasattr(active_layer,'source') and active_layer.source.path :
            image_path = active_layer.source.path
            output_dir = os.path.dirname(image_path)  
        rois = [entry["ROI"] for entry in self.analysis_data]
        cropped_layers = [entry["cropped"] for entry in self.analysis_data]
        # For each picture 
        for i in range(len(rois)):
            self.analysis_data[i]["FWHM"] = []
            self.analysis_data[i]["uncertainty"] = []
            self.analysis_data[i]["determination"] = []
            # Cropped picture extraction and creation of result folder
            image = cropped_layers[i]
            image_float = image.astype(np.float64)
            image_float = (image_float - np.min(image_float)) / (np.max(image_float) - np.min(image_float) + 1e-6)
            image_float[image_float < 0] = 0
            active_path = os.path.join(output_dir,f"bead_{i}")
            if not os.path.exists(active_path):
                os.makedirs(active_path)
            # Initialising global variables of the picture
            spacing = [self.parameters_acquisition["PhysicSizeZ"],self.parameters_acquisition["PhysicSizeY"],self.parameters_acquisition["PhysicSizeX"]]
            centroid_idx = self.analysis_data[i]["id"]
            physic = [int(self.filtered_beads[centroid_idx][0]), int(self.filtered_beads[centroid_idx][1] - rois[i][0][1]), int(self.filtered_beads[centroid_idx][2] - rois[i][0][2])]
            psf_z = image_float[:,physic[1],physic[2]]
            coords_z = np.arange(len(psf_z))
            #Gaussian fit for Z axis
            lim = [0,psf_z.max() * 1.1]
            bg = np.median(psf_z)
            amp = psf_z.max() - bg
            sigma = np.sqrt(get_cov_matrix(np.clip(psf_z - bg, 0, psf_z.max()), [spacing[0]], (self.filtered_beads[centroid_idx] - rois[i][0])))
            mu = np.argmax(psf_z)
            params,pcov,plt = fit_curve_1D(amp,bg,mu,sigma,coords_z,psf_z,lim)
            output_path = os.path.join(active_path, f'fit_curve_1D_Z.png')
            plt.savefig(output_path,dpi=300,bbox_inches='tight')
            plt.close()
            self.analysis_data[i]["FWHM"].append(fwhm(params[3]))
            self.analysis_data[i]["uncertainty"].append(uncertainty(pcov))
            self.analysis_data[i]["determination"].append(determination(params,coords_z,psf_z))
            # 2D Gaussian fit on YX stack
            psf_yx = image_float[physic[0],:,:]
            params,pcov,plt = fit_curve_2D(psf_yx,spacing)
            output_path = os.path.join(active_path, f'fit_curve_1D_YX.png')
            plt.savefig(output_path,dpi=300,bbox_inches='tight')
            plt.close()
            self.analysis_data[i]["FWHM"].append(fwhm(params[4]))
            self.analysis_data[i]["FWHM"].append(fwhm(params[6]))
            self.analysis_data[i]["uncertainty"].append(uncertainty(pcov))
            #self.analysis_data[i]["determination"].append(determination(params,coords_yx,psf_yx))
    

    def generate_pdf_report(self):
        """First version of a pdf generator to save analysis results on a pdf file"""
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
        else :
            output_path = default_path    
        # Creating a pdf canvas to save at output path        
        pdf = canvas.Canvas(output_path,pagesize=A4)
        pdf.setTitle("PSF analysis results")
        pdf.setFont("Helvetica-Bold", 36)
        pdf.drawCentredString(300,770, 'Results')
        stylesheet = getSampleStyleSheet()
        normalStyle = stylesheet['Normal']
        # Text Lines for general informations
        textLines = [
            f"Image location: {image_path}",
            f"Identified beads: {len(self.filtered_beads)}",
            f"Extracted ROIs: {len(rois)}",
            f"Signal to background ratio: {self.mean_SBR:.2f}"
        ]
        full_text = "<br/>".join(textLines)
        p = Paragraph(full_text,normalStyle)
        p.wrapOn(pdf,500,100)
        p.drawOn(pdf,40,680)
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawCentredString(300,600, 'Acquisition parameters')
        textLines = [
            f"Pixel size: [{self.parameters_acquisition["PhysicSizeZ"]},{self.parameters_acquisition["PhysicSizeY"]},{self.parameters_acquisition["PhysicSizeX"]}]",
            f"Image shape: [{self.parameters_acquisition["ShapeZ"]},{self.parameters_acquisition["ShapeY"]},{self.parameters_acquisition["ShapeX"]}]",
            f"Microscope type: {self.parameters_acquisition["Microscope_type"]}",
            f"Emission wavelength: {self.parameters_acquisition["Emission_Wavelength"]}nm",
            f"Refractive index: {self.parameters_acquisition["Refractive_index"]}",
            f"Numerical aperture: {self.parameters_acquisition["Numerical_aperture"]}"
        ]
        full_text = "<br/>".join(textLines)
        p = Paragraph(full_text,normalStyle)
        p.wrapOn(pdf,500,100)
        p.drawOn(pdf,40,500)
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawCentredString(300,400, 'Detection parameters')
        tools = ["peak_local_maxima", "blob_log", "blob_dog", "centroids"]
        textLines = [
            f"Detection method: {tools[self.parameters_detection['selected_tool']]}"
        ]
        if self.parameters_detection["selected_tool"] == 0:
            textLines.append(f"Minimal distance: {self.parameters_detection['Min_dist']}")
        else:
            textLines.append(f"Sigma: {self.parameters_detection['Sigma']}")
        textLines.extend([
            f"Bead size: {self.parameters_detection['theorical_bead_size']}",
            f"Crop factor: {self.parameters_detection['crop_factor']}"
        ])
        if self.parameters_detection["auto_threshold"]:
            textLines.append(f"Threshold tool: {self.parameters_detection['threshold_choice']}")
        else:
            textLines.append(f"Threshold relative: {self.parameters_detection['Rel_threshold']}")
        textLines.extend([
            f"Distance ring-bead: {self.parameters_detection['distance_annulus']}",
            f"Ring thickness: {self.parameters_detection['thickness_annulus']}"
        ])
        full_text = "<br/>".join(textLines)
        p = Paragraph(full_text, normalStyle)
        p.wrapOn(pdf, 500, 100)
        p.drawOn(pdf, 40, 300)

        # Break page and start to write report for each bead
        pdf.showPage()
        for i,psf in enumerate(cropped_layers):
            active_path = self.get_active_path(index=i)
            # Generating the HTML report
            self.generate_html_report(self.analysis_data[i],active_path,i)
            pdf.setFont("Helvetica-Bold", 36)
            pdf.drawCentredString(300,770, f'Bead_{i}')
            textLines = [
                f"centroid: {self.filtered_beads[self.analysis_data[i]["id"]]}",
                f"Full width at Half Maximum:",
                f"  Z: {self.analysis_data[i]["FWHM"][0]:.4f}",
                f"  Y: {self.analysis_data[i]["FWHM"][1]:.4f}",
                f"  X: {self.analysis_data[i]["FWHM"][2]:.4f}",
                f"Uncertainty: ",
                f"  Z: {self.analysis_data[i]["uncertainty"][0][3]:.4f}",
                f"  Y: {self.analysis_data[i]["uncertainty"][1][3]:.4f}",
                f"  X: {self.analysis_data[i]["uncertainty"][2][3]:.4f}",
                f"Determination: ",
                f"  Z: {self.analysis_data[i]["determination"][0]:.4f}",
                f"  Y: {self.analysis_data[i]["determination"][1]:.4f}",
                f"  X: {self.analysis_data[i]["determination"][2]:.4f}",
                f"Signal to background ratio: {self.analysis_data[i]["SBR"]:.2f}",
            ]
            text = pdf.beginText(40,680)
            text.setFont("Courier", 18)
            for line in textLines :
                text.textLine(line)
            pdf.drawText(text)
            pdf.showPage()
        # Save the PDF file
        pdf.save()


    def generate_html_report(self,psf,path,id_ROI):
        """Function to automatically generate the report of a bead analysis in a html file based on a template"""
        active_path = os.path.join(path,"PSF_analysis_result.html")
        template_dir = os.path.join(os.path.dirname(__file__),'res','template')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('report_template.html')
        data = {
            'title':id_ROI,
            'bead':self.filtered_beads[psf["id"]],
            'results':psf,
            'path':path
        }
        html_content = template.render(data)
        with open(active_path,'w') as f :
            f.write(html_content)


    def _open_browser(self):
        """Opens a webPage in a new window to display results of analysis"""
        active_path = self.get_active_path(index=self.selected_shape)
        active_path = os.path.join(active_path,"PSF_analysis_result.html")
        webbrowser.open(active_path)


    def _on_mouse_double_click(self,layer,event):
        """Called on mouse double click, detect if cursor is pointing a shape and open report for this one"""
        # Cursor position in the image
        click_pos = self.viewer.cursor.position
        # Do nothing if the Shapes layer doesn't exist
        if self.rois_layer is None :
            return
        # For each shape, test if contains the cursor
        for i,shape in enumerate(self.rois_layer.data):
            y_coords = [point[1] for point in shape]
            x_coords = [point[2] for point in shape]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            # If cursor is in the shape, open report and abort the loop
            if click_pos[1] >= y_min and click_pos[1] <= y_max and click_pos[2] >= x_min and click_pos[2] <= x_max:
                self.selected_shape = i
                self._open_browser()
                return
        



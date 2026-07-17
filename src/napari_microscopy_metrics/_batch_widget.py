import os
import napari
from napari.qt.threading import create_worker

from napari.utils.notifications import show_info
from qtpy.QtWidgets import (
    QPushButton,
    QWidget,
    QVBoxLayout,
    QLabel,
    QGroupBox,
    QSizePolicy,
    QHBoxLayout,
)
from qtpy.QtCore import Qt
from qtpy.QtGui import QFont, QIcon


class BatchWidget(QWidget):
    """A Napari widget for batch processing with improved styling and UX."""

    def __init__(self, viewer: "napari.viewer.Viewer", parent=None):
        super().__init__()
        self.viewer = viewer
        self._parent = parent
        self.Path = None
        self._init_ui()
        self._setup_connections()

    def _init_ui(self):
        """Initialize the widget UI with modern styling."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        description_group = QGroupBox()
        description_layout = QVBoxLayout()

        self.description_label = QLabel(
            "Batch processing will be applied to all images in the folder of the selected image. "
            "It will use the parameters saved in the plugin interface (or parameters of the previous analysis)."
        )
        self.description_label.setWordWrap(True)
        description_layout.addWidget(self.description_label)

        description_group.setLayout(description_layout)
        main_layout.addWidget(description_group)

        warning_group = QGroupBox()
        warning_layout = QVBoxLayout()

        self.warning_label = QLabel(
            "Warning: Batch processing will overwrite existing results in the output folder.\n"
            "Advice: Run the analysis on a single image first to check parameters and results."
        )
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("color: #8B0000;")
        warning_layout.addWidget(self.warning_label)

        warning_group.setLayout(warning_layout)
        main_layout.addWidget(warning_group)

        path_group = QGroupBox("Selected Folder")
        path_layout = QHBoxLayout()

        self.path_label = QLabel("No image selected")
        self.path_label.setStyleSheet("font-weight: bold; color: #2E8B57;")
        self.path_label.setWordWrap(True)
        path_layout.addWidget(self.path_label, stretch=1)

        self.copy_path_button = QPushButton("copy")
        self.copy_path_button.setIcon(QIcon.fromTheme("edit-copy"))
        self.copy_path_button.setToolTip("Copy folder path to clipboard")
        path_layout.addWidget(self.copy_path_button)

        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)

        action_layout = QHBoxLayout()

        self.run_batch_button = QPushButton("Run Batch Processing")
        self.run_batch_button.setToolTip(
            "Run batch processing on all images in the selected folder"
        )
        self.run_batch_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            """
        )
        self.run_batch_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        action_layout.addWidget(self.run_batch_button)

        main_layout.addLayout(action_layout)

        self.setLayout(main_layout)

        self.setStyleSheet(
            """
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                font-weight: bold;
            }
            """
        )

    def _setup_connections(self):
        """Set up signal connections."""
        self.viewer.layers.selection.events.active.connect(self._on_layer_changed)
        self.copy_path_button.clicked.connect(self._copy_path_to_clipboard)
        self.run_batch_button.clicked.connect(self._run_batch_processing)
        self._on_layer_changed()

    def _on_layer_changed(self):
        """Update the selected path when the active layer changes."""
        current_layer = self.viewer.layers.selection.active
        if current_layer is None or not isinstance(current_layer, napari.layers.Image):
            self.Path = None
            self.path_label.setText("No image selected")
            return

        image_path = (
            current_layer.source.path
            if hasattr(current_layer.source, "path")
            else "Unknown"
        )
        self.Path = os.path.dirname(image_path) if image_path != "Unknown" else None
        self.path_label.setText(
            f"Selected folder: {self.Path}" if self.Path else "No image selected"
        )

    def _copy_path_to_clipboard(self):
        """Copy the current path to the clipboard."""
        if self.Path:
            from qtpy.QtGui import QGuiApplication
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(self.Path)
            self.copy_path_button.setToolTip(f"Copied: {self.Path}")
            show_info(f"Path copied to clipboard: {self.Path}")

    def _run_batch_processing(self):
        """Run batch processing on all images in the selected folder."""
        if not self.Path:
            show_info("No folder selected for batch processing.")
            return
        self.worker = create_worker(
            self.analyzeBatch, _progress={"desc": "Analyzing batch..."}
        )
        self.worker.finished.connect(self.batchProcessingFinished)
        self.worker.errored.connect(self.batchProcessingError)
        self.worker.start()

    def analyzeBatch(self):
        """Run batch processing on all images in the selected folder."""
        if not self.Path:
            show_info("No folder selected for batch processing.")
            return
        self.run_batch_button.setEnabled(False)
        self.run_batch_button.setText("Processing...")
        batchAnalyzer = self._parent.generateBatchAnalyzer(self.Path)
        if batchAnalyzer is not None:
            show_info(f"Batch processing started for folder: {self.Path}")
            batchAnalyzer.analyze()
        else:
            show_info("Batch processing could not be started. Please check the parameters.")

    def batchProcessingError(self, error):
        """Handle errors during batch processing."""
        self.run_batch_button.setEnabled(True)
        self.run_batch_button.setText("Run Batch Processing")
        show_info(f"Batch processing error: {error}")

    def batchProcessingFinished(self):
        """Handle the completion of batch processing."""
        self.run_batch_button.setEnabled(True)
        self.run_batch_button.setText("Run Batch Processing")
        show_info("Batch processing completed.")
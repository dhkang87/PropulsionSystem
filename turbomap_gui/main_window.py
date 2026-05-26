"""Main window with 5-tab layout for the turbomap workflow."""
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar
from PyQt6.QtCore import pyqtSignal, QObject

from widgets.map_scaling_tab import MapScalingTab
from widgets.map_viewer_tab import MapViewerTab
from widgets.modelica_export_tab import ModelicaExportTab
from widgets.simulation_tab import SimulationTab
from widgets.opline_overlay_tab import OpLineOverlayTab


class AppSignals(QObject):
    """Cross-tab signals for data flow."""
    scaling_done = pyqtSignal(dict)    # emitted when scaling completes
    data_loaded = pyqtSignal(dict)     # emitted when simulation data is loaded


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TPE331 Turbomap Workflow")
        self.resize(1280, 820)

        # Shared application state
        self.app_state = {
            "compressor_parsed": None,
            "compressor_scaled": None,
            "ggt_parsed": None,
            "ggt_scaled": None,
            "fpt_parsed": None,
            "fpt_scaled": None,
            "sim_data": None,
        }
        self.signals = AppSignals()

        self._build_ui()

    def _build_ui(self):
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        self.tab_scaling = MapScalingTab(self.app_state, self.signals)
        self.tab_viewer = MapViewerTab(self.app_state, self.signals)
        self.tab_export = ModelicaExportTab(self.app_state, self.signals)
        self.tab_sim = SimulationTab(self.app_state, self.signals)
        self.tab_opline = OpLineOverlayTab(self.app_state, self.signals)

        tabs.addTab(self.tab_scaling, "1. Map Scaling")
        tabs.addTab(self.tab_viewer, "2. Map Viewer")
        tabs.addTab(self.tab_export, "3. Modelica Export")
        tabs.addTab(self.tab_sim, "4. Simulation")
        tabs.addTab(self.tab_opline, "5. Op-Line Overlay")

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

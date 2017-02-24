"""
Holder for the general UI operations
"""
import os

from ..ui.widgets.plugin import Plugin
from ..ui.widgets.utils import ICON_PATH
from ..ui.widgets.dialogs import KernelDialog

from ..analysis.filters import smooth


class ToolTrayPlugin(Plugin):
    """
    UI plugin for the general UI operations
    """
    name = "Tools"
    location = "hidden"
    priority = 0

    _all_categories = {}

    def setup_ui(self):
        self._smoothing_kernel_dialog = KernelDialog()

        # ---
        # Selections setup
        self.add_tool_bar_actions(
            name="Box ROI",
            description='Add box ROI',
            icon_path=os.path.join(ICON_PATH, "Rectangle Stroked-50.png"),
            category='Selections',
            enabled=False)

        # ---
        # Setup interactions buttons
        self.add_tool_bar_actions(
            name="Measure",
            description='Measure tool',
            icon_path=os.path.join(ICON_PATH, "Ruler-48.png"),
            category='Interactions',
            enabled=False)

        self.add_tool_bar_actions(
            name="Average",
            description='Average tool',
            icon_path=os.path.join(ICON_PATH, "Average Value-48.png"),
            category='Interactions',
            enabled=False)

        self.add_tool_bar_actions(
            name="Slice",
            description='Slice tool',
            icon_path=os.path.join(ICON_PATH, "Split Horizontal-48.png"),
            category='Interactions',
            enabled=False)

        # self.add_tool_bar_actions(
        #     name="Smooth",
        #     description='Smooth tool',
        #     icon_path=os.path.join(ICON_PATH, "Line Chart-48.png"),
        #     category='Interactions',
        #     enabled=False,
        #     callback=self._smoothing_kernel_dialog)

        # ---
        # Setup transformations buttons
        self.add_tool_bar_actions(
            name="Log Scale",
            description='Log scale plot',
            icon_path=os.path.join(ICON_PATH, "Combo Chart-48.png"),
            category='Transformations',
            enabled=False)

        # ---
        # Setup plot options
        self.add_tool_bar_actions(
            name="Export",
            description='Export plot',
            icon_path=os.path.join(ICON_PATH, "Export-48.png"),
            category='Options',
            enabled=False)

    def setup_connections(self):
        self._smoothing_kernel_dialog.accepted.connect(
            self._perform_smooth)

    def _perform_smooth(self):
        pass

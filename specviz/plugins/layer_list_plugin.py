"""
Plugin to manage the layers
"""
import logging
import os

import numpy as np
from astropy.units import spectral_density, spectral
from qtpy import compat
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from specviz.widgets.utils import ICON_PATH
from ..core.comms import dispatch, DispatchHandle
from ..core.data import Spectrum1DRefLayer, Spectrum1DRef
from ..widgets.dialogs import LayerArithmeticDialog
from ..widgets.plugin import Plugin


class LayerListPlugin(Plugin):
    """
    UI plugin to manage the data layers
    """
    name = "Layer List"
    location = "left"

    def __init__(self, *args, **kwargs):
        super(LayerListPlugin, self).__init__(*args, **kwargs)

        self._copied_model = None

    def setup_ui(self):
        UiLayerListPlugin(self)

        # Add tool tray buttons
        self.button_layer_slice = self.add_tool_bar_actions(
            name="Slice",
            description='Create layer slice',
            icon_path=os.path.join(ICON_PATH, "Stanley Knife-48.png"),
            category=('Transformations', 3),
            enabled=False,
            callback=lambda: self.add_layer(
                window=self.active_window, layer=self.current_layer,
                from_roi=True))

    def setup_connections(self):
        # -- Communications setup
        # Listen for layer selection events, enable/disable buttons
        self.tree_widget_layer_list.itemSelectionChanged.connect(
            lambda: self.toggle_buttons(self.current_layer_item))

        # Listen for layer selection events, update model tree on selection
        self.tree_widget_layer_list.itemSelectionChanged.connect(
            lambda: dispatch.on_selected_layer.emit(
                layer_item=self.current_layer_item))

        # When an interactable widget inside a layer item is clicked
        self.tree_widget_layer_list.itemClicked.connect(
            lambda li, col: dispatch.on_clicked_layer.emit(
                layer_item=li))

        # When an interactable widget inside a layer item is clicked
        self.tree_widget_layer_list.itemChanged.connect(
            lambda li, col: dispatch.on_changed_layer.emit(
                layer_item=li))

        # -- Widget connection setup
        # When the layer list delete button is pressed
        self.button_remove_layer.clicked.connect(lambda:
                                                 self.remove_layer_item())

        # When the arithmetic button is clicked, show math dialog
        self.button_layer_arithmetic.clicked.connect(
            self._show_arithmetic_dialog)

        # Create a new layer based on any active ROIs
        # self.button_create_layer_slice.clicked.connect(
        #     lambda: Dispatch.on_add_roi_layer.emit(layer=self.current_layer,
        #                                            from_roi=True))

        # Allow changing of plot color
        self.button_change_color.clicked.connect(
            self._change_plot_color)

        # Handle exporting layer objects
        self.button_export.clicked.connect(
            self._export_layer)

        self.button_copy_model.clicked.connect(
            self._copy_model)

        self.button_apply_model.clicked.connect(
            lambda: dispatch.on_paste_model.emit(layer=self.current_layer))

    def _export_layer(self):
        from astropy.io import registry as io_registry

        all_formats = io_registry.get_formats(Spectrum1DRef)['Format'].data
        writable_formats = io_registry.get_formats(Spectrum1DRef)['Write'].data

        write_mask = [True if x == 'Yes' else False for x in writable_formats]
        all_formats = all_formats[np.array(write_mask)]
        all_filters = ";;".join(list(all_formats))

        data = self.current_layer

        path, format = compat.getsavefilename(filters=all_filters)

        if path and format:
            data.write(path, format=format)

    def _copy_model(self):
        layer_item = self.current_layer_item
        layer = layer_item.data(0, Qt.UserRole)

        if hasattr(layer, 'model'):
            self._copied_model = layer

        if self._copied_model is not None:
            self.button_apply_model.setEnabled(True)
        else:
            self.button_apply_model.setEnabled(False)

    @DispatchHandle.register_listener("on_paste_model")
    def _paste_model(self, data=None, layer=None):
        if self._copied_model is None:
            logging.error("No copied model; unable to paste.")
            return

        if data is not None:
            layer = Spectrum1DRefLayer.from_parent(data)

        new_model_layer = self._copied_model.from_parent(parent=layer,
                                                         model=self._copied_model.model,
                                                         copy=True)

        if data is not None:
            dispatch.on_add_window.emit(layer=[layer, new_model_layer])
        else:
            dispatch.on_add_layer.emit(layer=new_model_layer)

    @property
    def current_layer(self):
        """
        Returns the currently selected layer object form the layer list widget.

        Returns
        -------
        layer : specviz.core.data.Spectrum1DRefLayer
            The `Layer` object of the currently selected row.
        """
        layer_item = self.tree_widget_layer_list.currentItem()

        if layer_item is not None:
            layer = layer_item.data(0, Qt.UserRole)

            return layer

    @property
    def current_layer_item(self):
        return self.tree_widget_layer_list.currentItem()

    @property
    def all_layers(self):
        layers = []
        root = self.tree_widget_layer_list.invisibleRootItem()

        for i in range(root.childCount()):
            child = root.child(i)

            if child.data(0, Qt.UserRole):
                layers.append(child.data(0, Qt.UserRole))

            for j in range(child.childCount()):
                sec_child = child.child(j)

                if sec_child.data(0, Qt.UserRole):
                    layers.append(sec_child.data(0, Qt.UserRole))

        return layers

    @DispatchHandle.register_listener("on_add_layer")
    def add_layer_item(self, layer, unique=True, *args, **kwargs):
        """
        Adds a `Layer` object to the loaded layer list widget.

        Parameters
        ----------
        layer : specviz.core.data.Spectrum1DRefLayer
            The `Layer` object to add to the list widget.
        """
        # Make sure there is only one item per layer object
        if unique:
            if self.get_layer_item(layer) is not None:
                return

        new_item = QTreeWidgetItem(
            self.get_layer_item(layer._parent) or
            self.tree_widget_layer_list)
        new_item.setFlags(
            new_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
        new_item.setText(0, layer.name)
        new_item.setData(0, Qt.UserRole, layer)
        new_item.setCheckState(0, Qt.Checked)

        self.tree_widget_layer_list.setCurrentItem(new_item)

    def get_layer_item(self, layer):
        root = self.tree_widget_layer_list.invisibleRootItem()

        for i in range(root.childCount()):
            child = root.child(i)

            if child.data(0, Qt.UserRole) == layer:
                return child

            for j in range(child.childCount()):
                sec_child = child.child(j)

                if sec_child.data(0, Qt.UserRole) == layer:
                    return sec_child

    @DispatchHandle.register_listener("on_remove_layer")
    def remove_layer_item(self, layer=None):
        if layer is None:
            layer = self.current_layer

        root = self.tree_widget_layer_list.invisibleRootItem()

        for i in range(root.childCount()):
            child = root.child(i)

            if child.data(0, Qt.UserRole) == layer:
                root.removeChild(child)
                break

            for j in range(child.childCount()):
                sec_child = child.child(j)

                if sec_child.data(0, Qt.UserRole) == layer:
                    child.removeChild(sec_child)
                    break

        dispatch.on_removed_layer.emit(layer=layer, window=self.active_window)

    def add_layer(self, layer=None, layer_mask=None, window=None, from_roi=True):
        """
        Creates a layer object from the current ROIs of the active plot layer.

        Parameters
        ----------
        layer : specviz.core.data.Spectrum1DRefLayer
            The current active layer of the active plot.
        window : QtGui.QMdiSubWindow
            The parent object within which the plot window resides.
        layer_mask : ndarray
            Boolean mask.
        """
        # User attempts to slice before opening a file
        if layer is None and window is None:
            logging.error(
                "Cannot add new layer; no layer and no window provided.")
            return

        roi_mask = layer_mask if layer_mask is not None and not from_roi else \
            window.get_roi_mask(layer=layer)

        new_layer = layer.from_self(layer_mask=roi_mask,
                                    name=layer.name + " Slice")

        dispatch.on_add_layer.emit(layer=new_layer, window=window)

    @DispatchHandle.register_listener("on_added_plot", "on_updated_plot")
    def update_layer_item(self, plot=None, *args, **kwargs):
        if plot is None:
            return

        layer = plot._layer
        pixmap = QPixmap(10, 10)
        pixmap.fill(plot.pen.color())
        icon = QIcon(pixmap)

        layer_item = self.get_layer_item(layer)

        if layer_item is not None:
            layer_item.setIcon(0, icon)
            layer_item.setCheckState(0, Qt.Checked if plot.checked else Qt.Unchecked)

    @DispatchHandle.register_listener("on_selected_layer", "on_changed_layer")
    def _update_layer_name(self, layer_item, checked_state=None, col=0):
        if layer_item is None:
            return

        layer = layer_item.data(0, Qt.UserRole)

        if self.active_window is not None:
            self.active_window.set_active_plot(layer)

        if hasattr(layer, 'name'):
            layer.name = layer_item.text(0)

        # Alert the statistics container to update the displayed layer name
        dispatch.on_updated_rois.emit(rois=None)

    def _show_arithmetic_dialog(self):
        if self.current_layer is None:
            return

        if self.dialog_layer_arithmetic.exec_():
            formula = self.dialog_layer_arithmetic\
                .line_edit_formula.text()

            current_window = self.active_window
            current_layers = self.all_layers

            # For whatever reason, parent_nddata in `NDUncertainty` objects are
            # weak references, and may, without warning, get garbage collected.
            # Re-do the the reference explicitly here to be sure it exists.
            for layer in current_layers:
                if layer.uncertainty is not None:
                    layer.uncertainty.parent_nddata = layer

            new_layer = Spectrum1DRefLayer.from_formula(formula,
                                                        current_layers)

            if new_layer is None:
                logging.warning("Formula not valid.")
                return

            # If units match, plot the resultant on the same sub window,
            # otherwise create a new sub window to plot the spectra
            data_units_equiv = new_layer.unit.is_equivalent(
                current_window._plot_units[1],
                equivalencies=spectral_density(new_layer.dispersion.data))

            disp_units_equiv = new_layer.dispersion_unit.is_equivalent(
                current_window._plot_units[0], equivalencies=spectral())

            if data_units_equiv and disp_units_equiv:
                dispatch.on_add_layer.emit(window=self.active_window,
                                           layer=new_layer)
            else:
                logging.info("{} not equivalent to {}.".format(
                    new_layer.unit, current_window._plot_units[1]))
                dispatch.on_add_window.emit(data=new_layer)

    def _change_plot_color(self):
        plot = self.active_window.get_plot(self.current_layer)

        col = QColorDialog.getColor(
            plot._pen_stash['pen_on'].color(),
            self.tree_widget_layer_list)

        if col.isValid():
            plot.pen = col

            dispatch.on_updated_plot.emit(plot=plot)
        else:
            logging.warning("Color is not valid.")

    def toggle_buttons(self, layer_item):
        if layer_item is not None:
            self.button_layer_arithmetic.setEnabled(True)
            self.button_remove_layer.setEnabled(True)
            self.button_layer_slice.setEnabled(True)
            self.button_change_color.setEnabled(True)
            self.button_export.setEnabled(True)

            layer = layer_item.data(0, Qt.UserRole)

            if hasattr(layer, 'model'):
                self.button_copy_model.setEnabled(True)
            else:
                self.button_copy_model.setEnabled(False)
        else:
            self.button_layer_arithmetic.setEnabled(False)
            self.button_remove_layer.setEnabled(False)
            self.button_layer_slice.setEnabled(False)
            self.button_change_color.setEnabled(False)
            self.button_export.setEnabled(True)

            self.button_copy_model.setEnabled(False)

    @DispatchHandle.register_listener("on_activated_window")
    def update_layer_list(self, window):
        self.tree_widget_layer_list.clear()

        if window is None:
            return

        layers = window.get_all_layers()

        for layer in layers:
            self.add_layer_item(layer)
            plot = window.get_plot(layer)
            self.update_layer_item(plot)

    @DispatchHandle.register_listener("on_clicked_layer")
    def _set_layer_visibility(self, layer_item, col=0):
        """
        Toggles the visibility of the plot in the sub window.

        Parameters
        ----------
        layer : Spectrum1DRefLayer
            Layer object to toggle visibility.

        col : int
            QtTreeWidget data column.
        """
        layer = layer_item.data(0, Qt.UserRole)
        current_window = self.active_window

        if layer is None or current_window is None:
            return

        plot = current_window.get_plot(layer)
        plot.checked = layer_item.checkState(col) == Qt.Checked

        current_window.set_active_plot(layer)


class UiLayerListPlugin:
    def __init__(self, plugin):
        plugin.layout_vertical.setContentsMargins(11, 11, 11, 11)

        plugin.tree_widget_layer_list = QTreeWidget(plugin)
        plugin.tree_widget_layer_list.setMinimumHeight(50)
        plugin.tree_widget_layer_list.setHeaderHidden(True)
        plugin.tree_widget_layer_list.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Ignored)

        plugin.layout_vertical.addWidget(plugin.tree_widget_layer_list)

        plugin.layout_horizontal = QHBoxLayout()

        plugin.button_layer_arithmetic = QToolButton(plugin)
        plugin.button_layer_arithmetic.setIcon(QIcon(os.path.join(
            ICON_PATH, "Math-48.png")))
        plugin.button_layer_arithmetic.setEnabled(False)
        plugin.button_layer_arithmetic.setIconSize(QSize(25, 25))
        plugin.button_layer_arithmetic.setMinimumSize(QSize(35, 35))

        plugin.button_copy_model = QToolButton(plugin)
        plugin.button_copy_model.setIcon(QIcon(os.path.join(
            ICON_PATH, "Copy-96.png")))
        plugin.button_copy_model.setEnabled(False)
        plugin.button_copy_model.setIconSize(QSize(25, 25))
        plugin.button_copy_model.setMinimumSize(QSize(35, 35))

        plugin.button_apply_model = QToolButton(plugin)
        plugin.button_apply_model.setIcon(QIcon(os.path.join(
            ICON_PATH, "Paste-96.png")))
        plugin.button_apply_model.setEnabled(False)
        plugin.button_apply_model.setIconSize(QSize(25, 25))
        plugin.button_apply_model.setMinimumSize(QSize(35, 35))

        plugin.button_remove_layer = QToolButton(plugin)
        plugin.button_remove_layer.setIcon(QIcon(os.path.join(
            ICON_PATH, "Delete-48.png")))
        plugin.button_remove_layer.setEnabled(False)
        plugin.button_remove_layer.setMinimumSize(QSize(35, 35))
        plugin.button_remove_layer.setIconSize(QSize(25, 25))

        plugin.button_change_color = QToolButton(plugin)
        plugin.button_change_color.setIcon(QIcon(os.path.join(
            ICON_PATH, "Color Dropper-48.png")))
        plugin.button_change_color.setEnabled(False)
        plugin.button_change_color.setMinimumSize(QSize(35, 35))
        plugin.button_change_color.setIconSize(QSize(25, 25))

        plugin.button_export = QToolButton(plugin)
        plugin.button_export.setIcon(QIcon(os.path.join(
            ICON_PATH, "Export-48.png")))
        plugin.button_export.setEnabled(False)
        plugin.button_export.setMinimumSize(QSize(35, 35))
        plugin.button_export.setIconSize(QSize(25, 25))
        plugin.button_export.setToolTip("Export spectrum to a file.")

        plugin.layout_horizontal.addWidget(plugin.button_layer_arithmetic)
        plugin.layout_horizontal.addWidget(plugin.button_copy_model)
        plugin.layout_horizontal.addWidget(plugin.button_apply_model)
        plugin.layout_horizontal.addStretch()
        plugin.layout_horizontal.addWidget(plugin.button_change_color)
        plugin.layout_horizontal.addWidget(plugin.button_export)
        plugin.layout_horizontal.addWidget(plugin.button_remove_layer)

        plugin.layout_vertical.addLayout(plugin.layout_horizontal)

        plugin.dialog_layer_arithmetic = LayerArithmeticDialog()

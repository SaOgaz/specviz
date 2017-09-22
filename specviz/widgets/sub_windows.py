from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys
import logging
from functools import reduce

import numpy as np
import pyqtgraph as pg
from itertools import cycle

from astropy.units import Quantity

from qtpy.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QLabel,
                            QLineEdit, QPushButton, QWidget)
from qtpy.QtCore import QEvent, Qt

from ..core.events import dispatch, dispatch
from ..core.linelist import ingest, LineList, WAVELENGTH_COLUMN, ID_COLUMN
from ..core.plots import LinePlot
from ..core.annotation import LineIDMarker
from .axes import DynamicAxisItem
from .region_items import LinearRegionItem
from .dialogs import ResampleDialog
from ..analysis.utils import resample

from .linelists_window import LineListsWindow


pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOptions(antialias=False)


AVAILABLE_COLORS = [
    (0, 0, 0),
    (0.2980392156862745, 0.4470588235294118, 0.6901960784313725),
    (0.3333333333333333, 0.6588235294117647, 0.40784313725490196),
    (0.7686274509803922, 0.3058823529411765, 0.3215686274509804),
    (0.5058823529411764, 0.4470588235294118, 0.6980392156862745),
    (0.8, 0.7254901960784313, 0.4549019607843137),
    (0.39215686274509803, 0.7098039215686275, 0.803921568627451),
    (0.2980392156862745, 0.4470588235294118, 0.6901960784313725),
    (0.3333333333333333, 0.6588235294117647, 0.40784313725490196),
    (0.7686274509803922, 0.3058823529411765, 0.3215686274509804),
    (0.5058823529411764, 0.4470588235294118, 0.6980392156862745)
]


class UiPlotSubWindow(QMainWindow):
    """
    Main plotting window.
    """
    def __init__(self, *args, **kwargs):
        super(UiPlotSubWindow, self).__init__(*args, **kwargs)

        self.vertical_layout = QVBoxLayout()
        self.horizontal_layout = QHBoxLayout()
        self.vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.vertical_layout.setSpacing(2)

        # X range
        self.label_x_range = QLabel()
        self.label_x_range.setText("X Range")
        self.line_edit_min_x_range = QLineEdit()
        self.line_edit_max_x_range = QLineEdit()

        self.layout_x_range = QHBoxLayout()
        self.layout_x_range.addWidget(self.label_x_range)
        self.layout_x_range.addWidget(self.line_edit_min_x_range)
        self.layout_x_range.addWidget(self.line_edit_max_x_range)

        # Y range
        self.label_y_range = QLabel()
        self.label_y_range.setText("Y Range")
        self.line_edit_min_y_range = QLineEdit()
        self.line_edit_max_y_range = QLineEdit()

        self.layout_y_range = QHBoxLayout()
        self.layout_y_range.addWidget(self.label_y_range)
        self.layout_y_range.addWidget(self.line_edit_min_y_range)
        self.layout_y_range.addWidget(self.line_edit_max_y_range)

        # Reset
        self.button_reset = QPushButton()
        self.button_reset.setText("Reset")

        # Cursor position
        self.line_edit_cursor_pos = QLabel()
        # self.line_edit_cursor_pos.setReadOnly(True)
        self.line_edit_cursor_pos.setText("Pos: 0, 0")

        # Line labels
        self._linelist_window = None
        self._line_labels = []

        self.horizontal_layout.addWidget(self.line_edit_cursor_pos)
        self.horizontal_layout.addStretch()
        # self.horizontal_layout.addLayout(self.layout_x_range)
        # self.horizontal_layout.addLayout(self.layout_y_range)
        self.horizontal_layout.addWidget(self.button_reset)

        self.vertical_layout.addLayout(self.horizontal_layout)

        self.main_widget = QWidget(self)
        self.main_widget.setLayout(self.vertical_layout)

        self.setCentralWidget(self.main_widget)


class PlotSubWindow(UiPlotSubWindow):
    """
    Sub window object responsible for displaying and interacting with plots.
    """
    def __init__(self, *args, **kwargs):
        super(PlotSubWindow, self).__init__(*args, **kwargs)
        self._plots = []
        self._dynamic_axis = None
        self._plot_widget = None
        self._plot_item = None
        self._plots_units = None
        self._rois = []
        self._measure_rois = []
        self._centroid_roi = None
        self._is_selected = True
        self._layer_items = []
        self.disable_errors = False
        self.disable_mask = True

        dispatch.setup(self)

        self._dynamic_axis = DynamicAxisItem(orientation='top')
        self._plot_widget = pg.PlotWidget(
            axisItems={'top': self._dynamic_axis})
        # self.setCentralWidget(self._plot_widget)
        self.vertical_layout.insertWidget(0, self._plot_widget)

        self._plot_item = self._plot_widget.getPlotItem()
        self._plot_item.showAxis('top', True)
        # Add grids to the plot
        self._plot_item.showGrid(True, True)

        self._setup_connections()

        self.linelists = []

        # Initial color list for this sub window
        self._available_colors = cycle(AVAILABLE_COLORS)

        # Incorporate event filter
        self.installEventFilter(self)

    def _setup_connections(self):
        # Connect cursor position to UI element
        # proxy = pg.SignalProxy(self._plot_item.scene().sigMouseMoved,
        #                        rateLimit=30, slot=self.cursor_moved)
        self._plot_item.scene().sigMouseMoved.connect(self.cursor_moved)
        self.button_reset.clicked.connect(self._reset_view)

    def cursor_moved(self, evt):
        pos = evt

        # Data range
        # flux = self._containers[0].data.value
        # disp = self._containers[0].dispersion.value

        # Plot range
        vb = self._plot_item.getViewBox()

        if self._plot_item.sceneBoundingRect().contains(pos):
            mouse_point = vb.mapSceneToView(pos)
            index = int(mouse_point.x())

            if index > 0 and index < vb.viewRange()[0][1]:
                self.line_edit_cursor_pos.setText("Pos: {0:4.4g}, "
                                                  "{1:4.4g}".format(
                    mouse_point.x(), mouse_point.y())
                    # flux[index], disp[index])
                )

    def _reset_view(self):
        view_box = self._plot_item.getViewBox()
        view_box.autoRange()

    def get_roi_mask(self, layer=None, container=None, roi=None):
        if layer is not None:
            container = self.get_plot(layer)

        if container is None:
            return

        mask = np.ones(layer.dispersion.shape, dtype=bool)
        mask_holder = []
        rois = [roi] if roi is not None else self._rois

        for roi in rois:
            # roi_shape = roi.parentBounds()
            # x1, y1, x2, y2 = roi_shape.getCoords()
            x1, x2 = roi.getRegion()

            mask = (container.layer.dispersion.data.value >= x1) & \
                   (container.layer.dispersion.data.value <= x2)

            mask_holder.append(mask)

        if len(mask_holder) > 0:
            mask = reduce(np.logical_or, mask_holder)
            mask = reduce(np.logical_and, [container.layer.layer_mask, mask])

        return mask

    def eventFilter(self, widget, event):
        if (event.type() == QEvent.KeyPress):
            key = event.key()

            if key == Qt.Key_Delete or key == Qt.Key_Backspace:
                for roi in self._rois:
                    if roi.mouseHovering:
                        roi.sigRemoveRequested.emit(roi)

                return True

        return QWidget.eventFilter(self, widget, event)

    def add_roi(self, bounds=None, *args, **kwargs):
        if bounds is None:
            view_range = self._plot_item.viewRange()
            x_len = (view_range[0][1] - view_range[0][0]) * 0.5
            x_pos = x_len * 0.5 + view_range[0][0]
            start, stop = x_pos, x_pos + x_len
        else:
            start, stop = bounds

        def remove():
            self._plot_item.removeItem(roi)
            self._rois.remove(roi)

        roi = LinearRegionItem(values=[start, stop])
        self._rois.append(roi)
        self._plot_item.addItem(roi)

        # Connect the remove functionality
        roi.sigRemoveRequested.connect(remove)

        # Connect events
        dispatch.on_updated_rois.emit(rois=self._rois)
        roi.sigRemoveRequested.connect(
            lambda: dispatch.on_updated_rois.emit(rois=self._rois))
        roi.sigRegionChangeFinished.connect(
            lambda: dispatch.on_updated_rois.emit(rois=self._rois))

    def get_roi_bounds(self):
        bounds = []

        for roi in self._rois:
            # roi_shape = roi.parentBounds()
            # x1, y1, x2, y2 = roi_shape.getCoords()
            bounds.append(list(roi.getRegion()))

        return bounds

    def get_plot(self, layer):
        for plot in self._plots:
            if plot.layer == layer:
                return plot

    def get_all_layers(self):
        return [plot.layer for plot in self._plots]

    def change_units(self, x=None, y=None, z=None):
        for cntr in self._plots:
            cntr.change_units(x, y, z)

        self.set_labels(x_label=x, y_label=y)
        self._plot_item.enableAutoRange()
        self._plot_units = [x, y, z]

    def set_labels(self, x_label='', y_label=''):
        self._plot_item.setLabels(
            left="Flux [{}]".format(
                y_label or str(self._plots[0].layer.unit)),
            bottom="Wavelength [{}]".format(
                x_label or str(self._plots[0].layer.dispersion_unit)))

    def set_visibility(self, layer, show_data, show_uncert, show_masked, inactive=None):
        plot = self.get_plot(layer)

        if plot is not None:
            plot.set_plot_visibility(show_data, inactive=inactive)
            plot.set_error_visibility(show_uncert)
            plot.set_mask_visibility(show_masked)

    def set_plot_style(self, layer, mode=None, line_width=None):
        plot = self.get_plot(layer)

        if mode is not None:
            plot.set_mode(mode)

        if line_width is not None:
            plot.set_line_width(line_width)

    def update_axis(self, layer=None, mode=None, **kwargs):
        self._dynamic_axis.update_axis(layer, mode, **kwargs)
        self._plot_widget.update()

    def update_plot_item(self):
        self._plot_item.update()

    @dispatch.register_listener("on_update_model")
    def update_plot(self, layer=None, plot=None):
        if layer is not None:
            plot = self.get_plot(layer)

            plot.update()

    def closeEvent(self, event):

        # before tearing down event handlers, need to close
        # any line lists window that might be still open.
        dispatch.on_dismiss_linelists_window.emit()

        dispatch.tear_down(self)
        super(PlotSubWindow, self).closeEvent(event)

    @dispatch.register_listener("on_add_layer")
    def add_plot(self, layer, window=None):
        if window is not None and window != self:
            return

        # Make sure the new plot layer has the same sampling as the current
        # layers
        def comp_disp(plot, layer):
            lstep = np.mean(layer.dispersion[1:] - layer.dispersion[:-1])
            pstep = np.mean(plot.layer.dispersion[1:] -
                            plot.layer.dispersion[:-1])

            return np.isclose(lstep.value, pstep.value)

        if not all(map(lambda p: comp_disp(p, layer=layer), self._plots)):
            logging.warning("New layer '{}' does not have the same dispersion "
                          "as current plot data.".format(layer.name))

            resample_dialog = ResampleDialog()

            if resample_dialog.exec_():
                in_data = np.ones(layer.dispersion.shape,
                                  [('wave', float),
                                   ('data', float),
                                   ('err', float)])

                in_data['wave'] = layer.dispersion.data.value
                in_data['data'] = layer.data.data.value
                in_data['err'] = layer.uncertainty.array

                plot = self._plots[0]

                out_data = resample(in_data, 'wave', plot.layer.dispersion.data.value,
                                    ('data', 'err'),
                                    kind=resample_dialog.method)

                new_data = layer.copy(
                    layer,
                    data=out_data['data'],
                    dispersion=out_data['wave'],
                    uncertainty=layer.uncertainty.__class__(out_data['err']),
                    dispersion_unit=layer.dispersion_unit)

                layer = layer.from_parent(
                    new_data,
                    name="Interpolated {}".format(layer.name),
                    layer_mask=layer.layer_mask)

        new_plot = LinePlot.from_layer(layer,
                                       color=next(self._available_colors))

        if len(self._plots) == 0:
            is_convert_success = self.change_units(
                new_plot.layer.dispersion_unit, new_plot.layer.unit)
        else:
            is_convert_success = new_plot.change_units(*self._plot_units)

            if not is_convert_success[0] or not is_convert_success[1]:
                logging.error("Unable to convert {} axis units of '{}' to current plot"
                              " units.".format('x' if not is_convert_success[0] else 'y',
                                               new_plot.layer.name))

                dispatch.on_remove_layer.emit(layer=layer)
                return

        if new_plot.error is not None:
            self._plot_item.addItem(new_plot.error)

        if new_plot.mask is not None:
            self._plot_item.addItem(new_plot.mask)

        self._plots.append(new_plot)
        self._plot_item.addItem(new_plot.plot)

        self.set_active_plot(new_plot.layer)

        # Make sure the dynamic axis object has access to a layer
        self._dynamic_axis._layer = self._plots[0].layer

        dispatch.on_added_layer.emit(layer=layer)
        dispatch.on_added_plot.emit(plot=new_plot, window=window)

    @dispatch.register_listener("on_removed_layer")
    def remove_plot(self, layer, window=None):
        if window is not None and window != self:
            return

        for plot in self._plots:
            if plot.layer == layer:
                self._plot_item.removeItem(plot.plot)

                if plot.error is not None:
                    self._plot_item.removeItem(plot.error)

                if plot.mask is not None:
                    self._plot_item.removeItem(plot.mask)

                self._plots.remove(plot)

    def set_active_plot(self, layer, checked_state=None):
        for plot in self._plots:
            if plot.checked:
                if plot.layer == layer:
                    self.set_visibility(plot.layer, True, not self.disable_errors, not self.disable_mask)
                else:
                    self.set_visibility(plot.layer, True, False, False)
            else:
                self.set_visibility(plot.layer, False, False, False)


#--------  Line lists and line labels handling.

    # Finds the wavelength range spanned by the spectrum (or spectra)
    # at hand. The range will be used to bracket the set of lines
    # actually read from the line list table(s).
    def _find_wavelength_range(self):
        # increasing dispersion values!
        amin = sys.float_info.max
        amax = 0.0

        for container in self._plots:
            amin = min(amin, container.layer.dispersion.compressed().value[0])
            amax = max(amax, container.layer.dispersion.compressed().value[-1])

        amin = Quantity(amin, self._plot_units[0])
        amax = Quantity(amax, self._plot_units[0])

        return (amin, amax)

    @dispatch.register_listener("on_request_linelists")
    def _request_linelists(self, *args, **kwargs):
        self.waverange = self._find_wavelength_range()

        self.linelists = ingest(self.waverange)

    @dispatch.register_listener("on_plot_linelists")
    def _plot_linelists(self, table_views, **kwargs):

        if not self._is_selected:
            return

        # Get a list of the selected indices in each line list.
        # Build new line lists with only the selected rows.

        linelists_with_selections = []

        for table_view in table_views:
            # Find matching line list by its name. This could be made
            # simpler by the use of a dict. That breaks code elsewhere
            # though: it is assumed by that code that self.linelists
            # is a list and not a dict.
            view_name = table_view.model().getName()
            for k in range(len(self.linelists)):
                line_list = self.linelists[k]
                line_list_name = line_list.name

                if line_list_name == view_name:
                    # must map between view and underlying model
                    # because of row sorting.
                    selected_rows = table_view.selectionModel().selectedRows()
                    model_selected_rows = []
                    for sr in selected_rows:
                        model_row = table_view.model().mapToSource(sr)
                        model_selected_rows.append(model_row)

                    new_list = line_list.extract_rows(model_selected_rows)

                    linelists_with_selections.append(new_list)

        # Merge all line lists into a single one. This might
        # change in the future to enable customized plotting
        # for each line list.
        merged_linelist = LineList.merge(linelists_with_selections)

        # Code below is plotting all markers at a fixed height in
        # the screen coordinate system. Still TBD how to do this in
        # the generic case. Maybe derive heights from curve data
        # instead? Make the markers follow the curve ups and downs?
        #
        # Ideally we would like to have the marker's X coordinate
        # pinned down to the plot surface in data value, and the Y
        # coordinate pinned down in screen value. This would make
        # the markers to stay at the same height in the window even
        # when the plot is zoomed. This kind of functionality doesn't
        # seem to be possible under pyqtgraph though. This requires
        # more investigation.

        plot_item = self._plot_item

        # curve = plot_item.curves[0]

        data_range = plot_item.vb.viewRange()
        ymin = data_range[1][0]
        ymax = data_range[1][1]
        height = (ymax - ymin) * 0.75 + ymin

        # column names are defined in the YAML files.
        wave_column = merged_linelist.columns[WAVELENGTH_COLUMN]
        id_column = merged_linelist.columns[ID_COLUMN]

        for i in range(len(wave_column)):
            marker = LineIDMarker(id_column[i], plot_item, orientation='vertical')

            marker.setPos(wave_column[i], height)

            plot_item.addItem(marker)
            self._line_labels.append(marker)

        plot_item.update()

    @dispatch.register_listener("on_erase_linelabels")
    def erase_linelabels(self, *args, **kwargs):
        if self._is_selected:
            for marker in self._line_labels:
                self._plot_item.removeItem(marker)
            self._plot_item.update()

    # The 3 handlers below, and their associated signals, implement
    # the logic that defines the show/hide/dismiss behavior of the
    # line list window. It remains to be seen if it is what users
    # actually want.

    @dispatch.register_listener("on_activated_window")
    def _set_selection_state(self, window):
        self._is_selected = window == self

        if self._linelist_window:
            if self._is_selected:
                self._linelist_window.show()
            else:
                self._linelist_window.hide()

    @dispatch.register_listener("on_show_linelists_window")
    def _show_linelists_window(self, *args, **kwargs):
        if self._is_selected:
            if self._linelist_window is None:
                self._linelist_window = LineListsWindow(self)
            self._linelist_window.show()

    @dispatch.register_listener("on_dismiss_linelists_window")
    def _dismiss_linelists_window(self, *args, **kwargs):
        if self._is_selected and self._linelist_window:
            self._linelist_window.hide()
            self._linelist_window = None
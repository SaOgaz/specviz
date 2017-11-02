import os

from glue.core import Subset
from qtpy.QtWidgets import QWidget

from glue.core.qt.data_combo_helper import ComponentIDComboHelper
from glue.utils.qt.widget_properties import CurrentComboDataProperty
from glue.utils.qt import load_ui

__all__ = ["OptionsWidget"]


class OptionsWidget(QWidget):

    file_att = CurrentComboDataProperty('ui.combo_file_attribute')

    def __init__(self, parent=None, data_viewer=None):

        super(OptionsWidget, self).__init__(parent=parent)

        self.ui = load_ui('viewer_options.ui', self,
                          directory=os.path.dirname(__file__))

        self.file_helper = ComponentIDComboHelper(self.ui.combo_file_attribute,
                                                  data_viewer._data)

        self._data_viewer = data_viewer

        self._data = None

    def set_data(self, data):
        self.file_helper.clear()

        if isinstance(data, Subset):
            self.file_helper.append_data(data.data)
        else:
            self.file_helper.append_data(data)

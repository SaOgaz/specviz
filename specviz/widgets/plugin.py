from abc import ABCMeta, abstractmethod, abstractproperty

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from specviz.core.comms import DispatchHandle


class PluginMeta(type):
    pass


class Plugin(QDockWidget):
    """
    Base object for plugin infrastructure.
    """
    __meta__ = ABCMeta

    location = 'hidden'
    priority = 1

    def __init__(self, parent=None):
        super(Plugin, self).__init__(parent)
        # Initialize this plugin's actions list
        self._actions = []

        # Keep a reference to the active sub window
        self._active_window = None
        self._current_layer = None

        DispatchHandle.setup(self)

        # GUI Setup
        self.setAllowedAreas(Qt.AllDockWidgetAreas)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setFrameShadow(QFrame.Plain)
        self.scroll_area.setLineWidth(0)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setGeometry(QRect(0, 0, 306, 553))

        # The main widget inside the scroll area
        self.contents = QWidget()
        self.layout_vertical = QVBoxLayout()
        self.layout_vertical.setContentsMargins(11, 11, 11, 11)
        self.layout_vertical.setSpacing(6)

        self.contents.setLayout(self.layout_vertical)
        self.scroll_area.setWidget(self.contents)

        self.setWidget(self.scroll_area)

        self.setWindowTitle(self.name)
        self.setup_ui()
        self.setup_connections()

    def _set_name(self, value):
        if isinstance(value, str):
            self.name = value
        else:
            raise TypeError("Inappropriate type for 'name' property.")

    def _get_name(self):
        return self.name

    name = abstractproperty(_set_name, _get_name)

    @abstractmethod
    def setup_ui(self):
        raise NotImplementedError()

    @abstractmethod
    def setup_connections(self):
        raise NotImplementedError()

    def _dict_to_menu(self, menu_dict, menu_widget=None):
        if menu_widget is None:
            menu_widget = QMenu()

        for k, v in menu_dict.items():
            if isinstance(v, dict):
                new_menu = menu_widget.addMenu(k)
                self._dict_to_menu(v, menu_widget=new_menu)
            else:
                act = QAction(k, menu_widget)

                if isinstance(v, list):
                    if v[0] == 'checkable':
                        v = v[1]
                        act.setCheckable(True)
                        act.setChecked(True)

                act.triggered.connect(v)
                menu_widget.addAction(act)

        return menu_widget

    def add_tool_bar_actions(self, icon_path, name="", category=None,
                             description="", priority=0, enabled=True,
                             callback=None, menu=None):
        icon = QIcon(icon_path)

        if menu is not None:
            tool_button = QToolButton()
            tool_button.setPopupMode(QToolButton.MenuButtonPopup)

            menu_widget = self._dict_to_menu(menu)

            tool_button.setMenu(menu_widget)
            tool_button.setIcon(icon)
            tool_button.setText(name)
            tool_button.setStatusTip(description)
            tool_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

            item = QWidgetAction(self)
            item.setDefaultWidget(tool_button)
            item.setEnabled(enabled)
        else:
            item = QAction(self)
            item.triggered.connect(callback if callback is not None else
                                     lambda: None)
            item.setIcon(icon)
            item.setStatusTip(description)
            item.setEnabled(enabled)
            item.setText(name)

        self._actions.append(dict(action=item,
                                  category=(category, 0) if not isinstance(
                                      category, tuple) else category,
                                  priority=priority))

        return item

    @property
    def active_window(self):
        return self._active_window

    @property
    def current_layer(self):
        return self._current_layer

    @DispatchHandle.register_listener("on_activated_window")
    def set_active_window(self, window):
        self._active_window = window

    @DispatchHandle.register_listener("on_selected_layer")
    def set_active_layer(self, layer_item):
        if layer_item is not None:
            self._current_layer = layer_item.data(0, Qt.UserRole)
        else:
            self._current_layer = None

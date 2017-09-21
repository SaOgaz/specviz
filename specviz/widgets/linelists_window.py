"""
Define all the line list-based windows and dialogs
"""
from qtpy.QtWidgets import (QWidget, QGridLayout, QHBoxLayout, QLabel,
                            QPushButton, QTabWidget, QVBoxLayout, QSpacerItem,
                            QMenu, QMenuBar, QSizePolicy, QToolBar, QStatusBar,
                            QAction, QTableView, QMainWindow,
                            QAbstractItemView, QLayout, QTextBrowser, QComboBox)
from qtpy.QtGui import QPixmap, QIcon, QColor
from qtpy.QtCore import (QSize, QRect, QCoreApplication, QMetaObject, Qt,
                         QAbstractTableModel, QVariant, QSortFilterProxyModel)

from ..core.comms import dispatch


#TODO work in progress

# The line list window must be a full fledged window and not a dialog.
# Dialogs do not support things like menu bars and central widgets.
# They are also a bit cumbersome to use when modal behavior is of no
# importance. Lets try to treat this as a window for now, and see how
# it goes.

class UiLinelistsWindow(object):

    # this code was taken as-is from the Designer.
    # Cleaning it up sounds like a lower priority
    # task for now.
    def setupUi(self, MainWindow, title):
        MainWindow.setWindowTitle(title)
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(600, 850)
        MainWindow.setMinimumSize(QSize(300, 350))
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.gridLayout = QGridLayout(self.centralWidget)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_5.setSpacing(6)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.lines_selected_label = QLabel(self.centralWidget)
        self.lines_selected_label.setObjectName("lines_selected_label")
        self.horizontalLayout_5.addWidget(self.lines_selected_label)
        self.label = QLabel(self.centralWidget)
        self.label.setObjectName("label")
        self.horizontalLayout_5.addWidget(self.label)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem)
        self.draw_button = QPushButton(self.centralWidget)
        self.draw_button.setObjectName("draw_button")
        self.horizontalLayout_5.addWidget(self.draw_button)
        self.erase_button = QPushButton(self.centralWidget)
        self.erase_button.setObjectName("erase_button")
        self.horizontalLayout_5.addWidget(self.erase_button)
        self.dismiss_button = QPushButton(self.centralWidget)
        self.dismiss_button.setObjectName("dismiss_button")
        self.horizontalLayout_5.addWidget(self.dismiss_button)
        self.gridLayout.addLayout(self.horizontalLayout_5, 4, 0, 1, 1)
        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_11.setSpacing(6)
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.tabWidget = QTabWidget(self.centralWidget)
        self.tabWidget.setObjectName("tabWidget")
        self.verticalLayout_11.addWidget(self.tabWidget)
        self.gridLayout.addLayout(self.verticalLayout_11, 0, 0, 1, 1)
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_7.setSpacing(6)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_7.addItem(spacerItem)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.gridLayout.addLayout(self.horizontalLayout_7, 2, 0, 2, 1)
        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QMenuBar(MainWindow)
        self.menuBar.setGeometry(QRect(0, 0, 767, 22))
        self.menuBar.setObjectName("menuBar")
        self.menuFile = QMenu(self.menuBar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menuBar)
        self.mainToolBar = QToolBar(MainWindow)
        self.mainToolBar.setMovable(False)
        self.mainToolBar.setFloatable(False)
        self.mainToolBar.setObjectName("mainToolBar")
        MainWindow.addToolBar(Qt.TopToolBarArea, self.mainToolBar)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)
        self.actionOpen = QAction(MainWindow)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/img/Open Folder-48.png"), QIcon.Normal, QIcon.Off)
        self.actionOpen.setIcon(icon)
        self.actionOpen.setObjectName("actionOpen")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionRemove = QAction(MainWindow)
        self.actionRemove.setObjectName("actionRemove")
        self.actionChange_Color = QAction(MainWindow)
        self.actionChange_Color.setObjectName("actionChange_Color")
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuBar.addAction(self.menuFile.menuAction())
        self.mainToolBar.addAction(self.actionOpen)
        self.mainToolBar.addSeparator()

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
        self.lines_selected_label.setText(_translate("MainWindow", "0"))
        self.label.setText(_translate("MainWindow", "lines selected"))
        self.draw_button.setText(_translate("MainWindow", "Draw"))
        self.erase_button.setText(_translate("MainWindow", "Erase"))
        self.dismiss_button.setText(_translate("MainWindow", "Dismiss"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionOpen.setText(_translate("MainWindow", "Open"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
        self.actionRemove.setText(_translate("MainWindow", "Remove"))
        self.actionRemove.setToolTip(_translate("MainWindow", "Removes the selected layer"))
        self.actionChange_Color.setText(_translate("MainWindow", "Change Color"))
        self.actionChange_Color.setToolTip(_translate("MainWindow", "Change the line color selected layer"))


class LineListsWindow(UiLinelistsWindow):
    def __init__(self, plot_window, parent=None):
        super(LineListsWindow, self).__init__()

        # Builds GUI
        self._main_window = QMainWindow()
        self.setupUi(self._main_window, str(plot_window))

        # Request that line lists be read from wherever are they sources.
        dispatch.on_request_linelists.emit()

        self.buildViews(plot_window)

        # Connect buttons to appropriate signals.
        #
        # Note that, for the Draw operation, we have to pass the table views to
        # the handler, even though it would be better to handle the row selections
        # all in here for the sake of encapsulation. This is so because this class
        # is not a QWidget or one of its subclasses, thus it cannot implement a
        # DispatchHandle signal handler.
        self.draw_button.clicked.connect(lambda:dispatch.on_plot_linelists.emit(
            table_views=self._table_views,
            units=plot_window.waverange[0].unit))
        self.erase_button.clicked.connect(dispatch.on_erase_linelabels.emit)
        self.dismiss_button.clicked.connect(dispatch.on_dismiss_linelists_window.emit)

    def buildViews(self, plot_window):

        # Table views must be preserved in the instance so they can be
        # passed to whoever is going to do the actual line list plotting.
        # The plotting code must know which lines (table rows) are selected
        # in each line list.
        self._table_views = []

        for linelist in plot_window.linelists:

            table_model = LineListTableModel(linelist)
            proxy = SortModel(table_model.getName())
            proxy.setSourceModel(table_model)

            if table_model.rowCount() > 0:
                table_view = QTableView()
                table_view.setModel(proxy)

                # setting this to False will significantly speed up
                # the loading of very large line lists. However, these
                # lists are often jumbled in wavelength, and consequently
                # difficult to read and use. It remains to be seen what
                # would be the approach users will favor.
                table_view.setSortingEnabled(True)

                table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
                table_view.horizontalHeader().setStretchLastSection(True)
                table_view.resizeColumnsToContents()
                comments = linelist.meta['comments']

                # this preserves the original sorting state
                # of the list. Use zero to sort by wavelength
                # on load. Doesn't seem to affect performance
                # by much tough.
                proxy.sort(-1, Qt.AscendingOrder)

                pane = self._buildLinelistPane(table_view, comments)

                self.tabWidget.addTab(pane, table_model.getName())

                self._table_views.append(table_view)

    def show(self):
        self._main_window.show()

    def hide(self):
        self._main_window.hide()

    def _buildLinelistPane(self, table, comments):
        pane = QWidget()

        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SetMaximumSize)
        pane.setLayout(layout)

        info = QTextBrowser()
        info.setMaximumHeight(100)
        info.setAutoFillBackground(True)
        info.setStyleSheet("background-color: rgb(230,230,230);")

        for comment in comments:
            info.append(comment)

        button_pane = QWidget()
        hlayout = QHBoxLayout()

        self.add_set_button = QPushButton(pane)
        self.add_set_button.setObjectName("add_set_button")
        _translate = QCoreApplication.translate
        self.add_set_button.setText(_translate("MainWindow", "Add set"))
        self.add_set_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        hlayout.addWidget(self.add_set_button)

        self.combo_box_color = QComboBox(pane)
        self.combo_box_color.setObjectName("color_selector")
        self.combo_box_color.addItems(QColor.colorNames())
        hlayout.addWidget(self.combo_box_color)

        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        hlayout.addItem(spacerItem)

        button_pane.setLayout(hlayout)

        layout.addWidget(info)
        layout.addWidget(table)
        layout.addWidget(button_pane)

        return pane


class LineListTableModel(QAbstractTableModel):

    def __init__(self, table, parent=None, *args):

        QAbstractTableModel.__init__(self, parent, *args)

        self._table = table

    def rowCount(self, index_parent=None, *args, **kwargs):
        return len(self._table.columns[0])

    def columnCount(self, index_parent=None, *args, **kwargs):
        return len(self._table.columns)

    def data(self, index, role=None):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        return QVariant(str(self._table.columns[index.column()][index.row()]))

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._table.colnames[section]
        return QAbstractTableModel.headerData(self, section, orientation, role)

    def getName(self):
        return self._table.name


class SortModel(QSortFilterProxyModel):

    def __init__(self, name):
        super(SortModel, self).__init__()

        self._name = name

    def lessThan(self, left, right):
        try:
            # first, we try comparing floats.
            left_data = left.data()
            left_float = float(left_data)
            right_data = right.data()
            right_float = float(right_data)

            return left_float < right_float

        except:
            # in case float conversion bombs out, we must force a
            # lexicographic string comparison. The parameters passed
            # to this method from a sortable table model are stored
            # in QtCore.QModelIndex instances.
            return str(left.data()) < str(right.data())

    def getName(self):
        return self._name

import json
import maya.cmds as cmds
import maya.mel as mel

from Qt import QtWidgets, QtCore
from Tools37.cute.widgets import MayaWidget37, AccordionWidget, FloatSliderWidget
from Tools37.maya import cute_utils as cu
from Tools37.maya.animation.olm_model import VertexModel


class OlmWidget(MayaWidget37):
    _TITLE = "Blendshape Controller"
    _WIDTH = 400

    signal_refresh_blendshape = QtCore.Signal()
    signal_set_blendshape = QtCore.Signal()

    signal_selection_mode = QtCore.Signal()
    signal_add_row = QtCore.Signal()
    signal_remove_row = QtCore.Signal()

    signal_import_selection = QtCore.Signal()
    signal_export_selection = QtCore.Signal()

    signal_vertex_sphere_size = QtCore.Signal(float)
    signal_control_sphere_size = QtCore.Signal(float)

    def __init__(self, stay_top=True, parent=None):
        super(OlmWidget, self).__init__(parent)
        self._blendshape_combox = None
        self._set_button = None
        self._table_view = None
        self._table_model = None
        self._init(stay_top)

    def _get_object_name(self):
        return "OLM_Widget"

    def _get_window_title(self):
        return "Blendshape Controller"

    # Interface #

    def _init(self, stay_top):
        self.setWindowTitle(self._TITLE)
        self.setFixedWidth(self._WIDTH)
        if stay_top:
            self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        self.setLayout(QtWidgets.QVBoxLayout())

        accordion = AccordionWidget(self)
        accordion.setRolloutStyle(accordion.Maya)
        accordion.setSpacing(0)
        self.layout().addWidget(accordion)

        widget, self._blendshape_combox, self._set_button = self._create_blendshape_widget()
        accordion.addItem("Blendshape", widget)

        widget, self._table_model = self._create_vertex_widget()
        accordion.addItem("Vertex Controllers", widget)

        widget = self._create_sphere_widget()
        accordion.addItem("Sphere Options", widget)

        widget = self._create_import_export_widget()
        accordion.addItem("Import|Export", widget)

    def _create_blendshape_widget(self):
        grid_layout = QtWidgets.QGridLayout()
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 2)
        grid_layout.setColumnStretch(2, 1)

        label = QtWidgets.QLabel("<b>Blendshapes</b>")
        grid_layout.addWidget(label, 0, 0)

        blendshape_combox = QtWidgets.QComboBox()
        blendshape_combox.addItems(self._get_blendshapes())
        grid_layout.addWidget(blendshape_combox, 0, 1)

        button = QtWidgets.QPushButton()
        button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
        button.setIconSize(QtCore.QSize(20, 20))
        button.clicked.connect(self.signal_refresh_blendshape.emit)
        grid_layout.addWidget(button, 0, 2)

        button = QtWidgets.QPushButton("Use Blendshape")
        button.clicked.connect(self.signal_set_blendshape.emit)
        grid_layout.addWidget(button, 1, 0, 1, 3)

        widget = QtWidgets.QWidget()
        widget.setLayout(grid_layout)
        return widget, blendshape_combox, button

    def _create_vertex_widget(self):
        table_model = VertexModel()

        def highlight(index):
            self._table_model.highlight(index.row())

        table_view = QtWidgets.QTableView()
        table_view.setModel(table_model)
        table_view.clicked[QtCore.QModelIndex].connect(highlight)
        table_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table_view.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        for i in range(table_view.horizontalHeader().count()):
            table_view.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(table_view)

        space = QtWidgets.QSpacerItem(16, 16, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        layout.addItem(space)

        button = QtWidgets.QPushButton("Enter Vertex Selection")
        button.clicked.connect(self.signal_selection_mode.emit)
        layout.addWidget(button)

        button = QtWidgets.QPushButton("Add Vertex")
        button.clicked.connect(self.signal_add_row.emit)
        layout.addWidget(button)

        space = QtWidgets.QSpacerItem(16, 16, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        layout.addItem(space)

        button = QtWidgets.QPushButton("Delete Vertex")
        button.clicked.connect(self.signal_remove_row.emit)
        layout.addWidget(button)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        return widget, table_model

    def _create_sphere_widget(self):
        layout = QtWidgets.QVBoxLayout()

        vertex_sphere_size = FloatSliderWidget(title="Vertex Scale", min_value=0.0, max_value=1.0, start_value=self._table_model._SPHERE_DEF_SIZE)
        vertex_sphere_size.signal_value_changed.connect(self.signal_vertex_sphere_size.emit)
        layout.addWidget(vertex_sphere_size)

        control_sphere_size = FloatSliderWidget(title="Controller Scale", min_value=0.0, max_value=1.0, start_value=self._table_model._SPHERE_DEF_SIZE)
        control_sphere_size.signal_value_changed.connect(self.signal_control_sphere_size.emit)
        layout.addWidget(control_sphere_size)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

    def _create_import_export_widget(self):
        layout = QtWidgets.QVBoxLayout()

        button = QtWidgets.QPushButton("Import")
        button.clicked.connect(self._import)
        layout.addWidget(button)

        button = QtWidgets.QPushButton("Export")
        button.clicked.connect(self._export)
        layout.addWidget(button)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

    # Data #

    @classmethod
    def _get_blendshapes(cls):
        """ Returns a string list of blendshapes names. """
        raise NotImplementedError()

    # Close #

    def closeEvent(self, event):
        # TODO; does not work with the Mixin in Maya 2017.
        self._table_model.delete()
        return super(OlmWidget, self).closeEvent(event)

from napari._qt.layer_controls.qt_points_controls import QtPointsControls
from napari._qt.layer_controls.widgets.qt_widget_controls_base import QtWrappedLabel
from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget


class CustomQtManualPointsControls(QtPointsControls):
    """Custom Qt controls for editable points layers with undo/redo."""

    def __init__(self, layer):
        super().__init__(layer)

        self._projection_mode_control.projection_combobox.setHidden(True)
        self._projection_mode_control.projection_combobox_label.setHidden(True)
        self._symbol_combobox_control.symbol_combobox.setHidden(True)
        self._symbol_combobox_control.symbol_combobox_label.setHidden(True)
        self._text_visibility_control.text_disp_checkbox.setHidden(True)
        self._text_visibility_control.text_disp_label.setHidden(True)
        self._out_slice_checkbox_control.out_of_slice_checkbox.setHidden(True)
        self._out_slice_checkbox_control.out_of_slice_checkbox_label.setHidden(True)

        self._undo_button = QPushButton("Undo")
        self._redo_button = QPushButton("Redo")
        self._undo_button.clicked.connect(layer.undo)
        self._redo_button.clicked.connect(layer.redo)

        history_widget = QWidget(self)
        history_layout = QHBoxLayout(history_widget)
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_layout.addWidget(self._undo_button)
        history_layout.addWidget(self._redo_button)

        self.layout().insertRow(0, QtWrappedLabel("History:"), history_widget)

        def _sync_buttons(_event=None):
            self._undo_button.setEnabled(layer.can_undo)
            self._redo_button.setEnabled(layer.can_redo)

        layer.events.history.connect(_sync_buttons)
        layer.events.data.connect(_sync_buttons)
        _sync_buttons()

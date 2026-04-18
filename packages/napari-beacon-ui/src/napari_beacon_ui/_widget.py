from qtpy.QtCore import Qt
from qtpy.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QWidget

from .ui_modifications import (
    _state,
    disable_layer_controls,
    disable_orientation_buttons,
    enable_layer_controls,
    enable_orientation_buttons,
    hide_viewer_buttons,
    show_viewer_buttons,
)


class BeaconUIWidget(QWidget):
    def __init__(self, viewer):
        super().__init__()
        self._viewer = viewer

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("BEACON UI toggles"))

        self.orientation_toggle = QCheckBox("Orientation buttons (A/C/S)")
        self.viewer_buttons_toggle = QCheckBox("Hide default viewer buttons")
        self.layer_controls_toggle = QCheckBox("Lock layer controls")

        layout.addWidget(self.orientation_toggle)
        layout.addWidget(self.viewer_buttons_toggle)
        layout.addWidget(self.layer_controls_toggle)

        self.orientation_toggle.stateChanged.connect(self._on_orientation_toggled)
        self.viewer_buttons_toggle.stateChanged.connect(self._on_viewer_buttons_toggled)
        self.layer_controls_toggle.stateChanged.connect(self._on_layer_controls_toggled)

        self._sync_from_state()

    def _on_orientation_toggled(self, state):
        if state == Qt.CheckState.Checked.value:
            enable_orientation_buttons(self._viewer)
        else:
            disable_orientation_buttons(self._viewer)

    def _on_viewer_buttons_toggled(self, state):
        if state == Qt.CheckState.Checked.value:
            hide_viewer_buttons(self._viewer)
        else:
            show_viewer_buttons(self._viewer)

    def _on_layer_controls_toggled(self, state):
        if state == Qt.CheckState.Checked.value:
            disable_layer_controls(self._viewer)
        else:
            enable_layer_controls(self._viewer)

    def _sync_from_state(self):
        state = _state(self._viewer)

        self.orientation_toggle.blockSignals(True)
        self.viewer_buttons_toggle.blockSignals(True)
        self.layer_controls_toggle.blockSignals(True)

        self.orientation_toggle.setChecked(bool(state.orientation_buttons))
        self.viewer_buttons_toggle.setChecked(state.viewer_buttons_hidden)
        self.layer_controls_toggle.setChecked(state.layers_controls_locked)

        self.orientation_toggle.blockSignals(False)
        self.viewer_buttons_toggle.blockSignals(False)
        self.layer_controls_toggle.blockSignals(False)

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_from_state()

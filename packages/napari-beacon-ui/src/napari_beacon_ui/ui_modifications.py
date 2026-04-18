from __future__ import annotations

from dataclasses import dataclass, field

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QPushButton


_STATE_ATTR = "_napari_beacon_ui_state"


@dataclass
class BeaconUIState:
    orientation_buttons: list[QPushButton] = field(default_factory=list)
    layers_keypress_handler: object | None = None
    viewer_buttons_hidden: bool = False
    layers_controls_locked: bool = False


def _state(viewer) -> BeaconUIState:
    state = getattr(viewer, _STATE_ATTR, None)
    if state is None:
        state = BeaconUIState()
        setattr(viewer, _STATE_ATTR, state)
    return state


def set_axial(viewer):
    viewer.dims.order = (0, 1, 2)


def set_coronal(viewer):
    viewer.dims.order = (1, 0, 2)


def set_saggital(viewer):
    viewer.dims.order = (2, 0, 1)


def enable_orientation_buttons(viewer):
    state = _state(viewer)
    if state.orientation_buttons:
        return

    viewer_buttons = viewer.window._qt_viewer._viewerButtons
    layout = viewer_buttons.layout()

    for text, callback in (("A", set_axial), ("C", set_coronal), ("S", set_saggital)):
        button = QPushButton(text)
        button.clicked.connect(lambda _checked=False, cb=callback: cb(viewer))
        button.setStyleSheet(
            """
            min-width : 28px;
            max-width : 28px;
            min-height : 28px;
            max-height : 28px;
            padding: 0px;
            """
        )
        layout.insertWidget(-1, button)
        state.orientation_buttons.append(button)


def disable_orientation_buttons(viewer):
    state = _state(viewer)
    layout = viewer.window._qt_viewer._viewerButtons.layout()

    for button in state.orientation_buttons:
        layout.removeWidget(button)
        button.setParent(None)
        button.deleteLater()
    state.orientation_buttons.clear()


def toggle_orientation_buttons(viewer):
    state = _state(viewer)
    if state.orientation_buttons:
        disable_orientation_buttons(viewer)
    else:
        enable_orientation_buttons(viewer)


def hide_viewer_buttons(viewer):
    viewer_buttons = viewer.window._qt_viewer._viewerButtons
    viewer_buttons.rollDimsButton.setHidden(True)
    viewer_buttons.transposeDimsButton.setHidden(True)
    viewer_buttons.consoleButton.setHidden(True)
    viewer_buttons.gridViewButton.setHidden(True)
    viewer_buttons.ndisplayButton.setHidden(True)
    _state(viewer).viewer_buttons_hidden = True


def show_viewer_buttons(viewer):
    viewer_buttons = viewer.window._qt_viewer._viewerButtons
    viewer_buttons.rollDimsButton.setHidden(False)
    viewer_buttons.transposeDimsButton.setHidden(False)
    viewer_buttons.consoleButton.setHidden(False)
    viewer_buttons.gridViewButton.setHidden(False)
    viewer_buttons.ndisplayButton.setHidden(False)
    _state(viewer).viewer_buttons_hidden = False


def toggle_viewer_buttons(viewer):
    state = _state(viewer)
    if state.viewer_buttons_hidden:
        show_viewer_buttons(viewer)
    else:
        hide_viewer_buttons(viewer)


def disable_layer_controls(viewer):
    state = _state(viewer)
    qt_viewer = viewer.window._qt_viewer
    qt_viewer._layersButtons.setHidden(True)

    if state.layers_keypress_handler is None:
        previous = qt_viewer._layers.keyPressEvent

        def patched(event, _previous=previous):
            if event is None:
                return
            if event.key() in (
                Qt.Key.Key_Backspace,
                Qt.Key.Key_Delete,
                Qt.Key.Key_Enter,
                Qt.Key.Key_Return,
            ):
                event.ignore()
                return
            _previous(event)

        qt_viewer._layers.keyPressEvent = patched
        state.layers_keypress_handler = previous

    state.layers_controls_locked = True


def enable_layer_controls(viewer):
    state = _state(viewer)
    qt_viewer = viewer.window._qt_viewer
    qt_viewer._layersButtons.setHidden(False)

    if state.layers_keypress_handler is not None:
        qt_viewer._layers.keyPressEvent = state.layers_keypress_handler
        state.layers_keypress_handler = None

    state.layers_controls_locked = False


def toggle_layer_controls(viewer):
    state = _state(viewer)
    if state.layers_controls_locked:
        enable_layer_controls(viewer)
    else:
        disable_layer_controls(viewer)


def apply_artist_study_ui(viewer):
    enable_orientation_buttons(viewer)
    hide_viewer_buttons(viewer)
    disable_layer_controls(viewer)


def revert_artist_study_ui(viewer):
    show_viewer_buttons(viewer)
    enable_layer_controls(viewer)
    disable_orientation_buttons(viewer)


def toggle_artist_study_ui(viewer):
    state = _state(viewer)
    if state.orientation_buttons and state.viewer_buttons_hidden and state.layers_controls_locked:
        revert_artist_study_ui(viewer)
    else:
        apply_artist_study_ui(viewer)

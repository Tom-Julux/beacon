import numpy as np
from napari.layers import Points
from napari.utils.events import Event

from napari._qt.layer_controls.qt_layer_controls_container import layer_to_controls
from napari_beacon_layers.controls.manual_points_control import CustomQtManualPointsControls


class ManualPointsLayer(Points):
    """Editable points layer with undo/redo history.

    Emits a custom ``history`` event whenever the undo/redo state changes
    (new snapshot, undo, redo) so UI controls can refresh enabled states.
    """

    def __init__(self, data, *args, max_history=100, **kwargs):
        super().__init__(data, *args, **kwargs)
        self._max_history = max(1, int(max_history))
        self._history = [self._snapshot_data()]
        self._history_index = 0
        self._is_restoring_history = False

        self.events.add(history=Event)
        self.events.data.connect(self._on_data_change)
        self._bind_shortcuts()

    def _bind_shortcuts(self):
        def _bind_shortcut(shortcut, action):
            @self.bind_key(shortcut, overwrite=True)
            def _run(_viewer):
                action()

        for shortcut in ("Control-Z", "Meta-Z"):
            _bind_shortcut(shortcut, self.undo)

        for shortcut in ("Control-Y", "Control-Shift-Z", "Meta-Shift-Z"):
            _bind_shortcut(shortcut, self.redo)

    def _snapshot_data(self) -> np.ndarray:
        return np.asarray(self.data).copy()

    def _on_data_change(self, event=None):
        if self._is_restoring_history:
            return

        current = self._snapshot_data()
        previous = self._history[self._history_index]
        if current.shape == previous.shape and np.array_equal(current, previous):
            return

        self._history = self._history[: self._history_index + 1]
        self._history.append(current)
        self._history_index = len(self._history) - 1

        if len(self._history) > self._max_history:
            overflow = len(self._history) - self._max_history
            self._history = self._history[overflow:]
            self._history_index = len(self._history) - 1

        self.events.history()

    @property
    def can_undo(self) -> bool:
        return self._history_index > 0

    @property
    def can_redo(self) -> bool:
        return self._history_index < len(self._history) - 1

    def _restore_history_state(self):
        self._is_restoring_history = True
        try:
            self.data = self._history[self._history_index].copy()
            self.selected_data = set()
        finally:
            self._is_restoring_history = False
        self.refresh()

    def undo(self) -> bool:
        if not self.can_undo:
            return False
        self._history_index -= 1
        self._restore_history_state()
        self.events.history()
        return True

    def redo(self) -> bool:
        if not self.can_redo:
            return False
        self._history_index += 1
        self._restore_history_state()
        self.events.history()
        return True


# register the custom layer controls
layer_to_controls[ManualPointsLayer] = CustomQtManualPointsControls

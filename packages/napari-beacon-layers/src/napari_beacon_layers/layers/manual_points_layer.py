from collections import deque
from contextlib import contextmanager

import numpy as np
from napari.layers import Points
from napari.utils.events import Event

from napari._qt.layer_controls.qt_layer_controls_container import layer_to_controls
from napari_beacon_layers.controls.manual_points_control import CustomQtManualPointsControls


class ManualPointsLayer(Points):
    """Editable points layer with keyboard-driven undo/redo history.

    Emits a custom ``history`` event whenever the undo/redo state changes
    (new snapshot, undo, redo) so listeners can react to history updates.
    """

    def __init__(self, data, *args, max_history=100, **kwargs):
        super().__init__(data, *args, **kwargs)
        self._history_limit = max(1, int(max_history))
        self._reset_history()
        self._last_history_state = self._snapshot_data()
        self._is_restoring_history = False

        self.events.add(history=Event)
        self.events.data.connect(self._on_data_change)

    def _snapshot_data(self) -> np.ndarray:
        return np.asarray(self.data).copy()

    def _reset_history(self, event: Event | None = None) -> None:
        self._undo_history = deque(maxlen=self._history_limit)
        self._redo_history = deque(maxlen=self._history_limit)
        self._staged_history = []
        self._block_history = False

    @contextmanager
    def block_history(self):
        prev = self._block_history
        self._block_history = True
        try:
            yield
            self._commit_staged_history()
        finally:
            self._block_history = prev

    def _commit_staged_history(self):
        if self._staged_history:
            self._append_to_undo_history(self._staged_history)
            self._staged_history = []

    def _append_to_undo_history(self, item):
        self._undo_history.append(item)
        self.events.history()

    def _save_history(self, value):
        self._redo_history.clear()
        if self._block_history:
            self._staged_history.append(value)
        else:
            self._append_to_undo_history([value])

    def _on_data_change(self, event=None):
        if hasattr(event, "action") and event.action in ["adding", "removing", "changing"]:
            return

        if self._is_restoring_history:
            return

        current = self._snapshot_data()
        previous = self._last_history_state
        if current.shape == previous.shape and np.array_equal(current, previous):
            return
        self._save_history((previous.copy(), current.copy()))
        self._last_history_state = current

    @property
    def can_undo(self) -> bool:
        return len(self._undo_history) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_history) > 0

    def _load_history(self, before, after, undoing=True):
        if len(before) == 0:
            return False

        history_item = before.pop()
        after.append(list(reversed(history_item)))

        self._is_restoring_history = True
        try:
            for previous_data, next_data in reversed(history_item):
                restored = previous_data if undoing else next_data
                self.data = restored.copy()
            self.selected_data = set()
        finally:
            self._is_restoring_history = False
        self._last_history_state = self._snapshot_data()
        self.refresh()
        self.events.history()
        return True

    def undo(self) -> bool:
        return self._load_history(self._undo_history, self._redo_history, undoing=True)

    def redo(self) -> bool:
        return self._load_history(self._redo_history, self._undo_history, undoing=False)


# register the custom layer controls
layer_to_controls[ManualPointsLayer] = CustomQtManualPointsControls

ManualPointsLayer.bind_key("Control-Z", ManualPointsLayer.undo)
ManualPointsLayer.bind_key("Control-Shift-Z", ManualPointsLayer.redo)

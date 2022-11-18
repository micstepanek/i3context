import subprocess
import threading

import i3ipc
from PySide6.QtCore import QObject, Signal

import i3ipc_patch


class I3(i3ipc.Connection):
    def __init__(self):
        i3ipc_patch.apply()
        super(I3, self).__init__(auto_reconnect=True)
        self.cache = I3Cache()
        self.listener = I3Listener()

    def init_2(self):
        self.cache.update()
        self.listener.listen_for_bindings()

    def mode_default(self):
        self.command('mode default')

    def get_new_workspace_container(self):
        return self.get_tree().workspaces()[0]


class I3Listener:
    def listen_for_bindings(self):
        i3.on(i3ipc.Event.BINDING, self.filter_binding_events)
        threading.Thread(target=i3.main).start()

    def filter_binding_events(self, _, event):
        if event.binding.command.endswith('i3context'):
            signals.binding.emit(event)


class I3Cache:
    def __init__(self):
        self.tree = None
        self.workspaces = None
        self.current_workspace = None
        self.focused_window = None

    def update(self):
        self.tree = i3.get_tree()
        self.workspaces = self.tree.workspaces()
        self.focused_window = self.tree.find_focused()
        self.current_workspace = self.focused_window.workspace()


class Signals(QObject):
    binding = Signal(object)

signals = Signals()
i3 = I3()
i3.init_2()

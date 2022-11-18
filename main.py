

#!/usr/bin/env python3.8
"""
"""
import logging
import subprocess
import time

import pyautogui
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication
# modules
import graphical_elements
import i3ipc_interface
import file_handler

logger = logging.getLogger(__name__)

class Launcher:
    def fork(self, string):
        command = ['launcher.sh']
        command.extend(string.split())
        subprocess.run(command)
        gui.hide_and_reset()


class GUI:
    def __init__(self):
        self.widget = graphical_elements.MainWidget()
        # override Escape key behavior
        self.widget.reject = self.hide_and_reset
        self.position = 0
        self.workspace_mode = False
        self.sublist = None
        self.retag_mode = False

    def wake_up(self):
        i3.cache.update()
        self._prepare_position()
        self.widget.clear()
        self.widget.reappear()
        if i3.cache.focused_window.floating in ['auto_on', 'user_on']:
            i3.command('[instance="i3context.py"] focus')

    def prepare_for_retag_entry(self):
        #i3.command('[instance="i3context.py"] focus')
        #subprocess.run(['xdotool','getwindowfocus','windowfocus'])
        #the above is not working, focusing done in i3 config
        tags.update()
        self._prepare_tags()
        i3.mode_default()
        gui.widget.show_retag_entry()

    def _self_reset(self):
        self.widget.self_reset()
        self.position = 0
        self.workspace_mode = False
        #self.retag_mode = False

    @Slot()
    def handle_binding(self, event):
        symbol = event.binding.symbol
        logging.debug([symbol])
        if event.binding.command.endswith('mode i3context'):
            self.wake_up()
        elif symbol == 'Escape':
            self.hide_and_reset()
        elif symbol == 'ISO_Level3_Latch':
            self.workspace_mode = True
            tags.update()
            self.widget.clear()
            self._prepare_tags()
            self.widget.reappear()
        elif symbol == 'Return':
            self.hide_and_reset()
            # sending messages in Slack
            pyautogui.keyUp('enter')
            pyautogui.hotkey('ctrl', 'enter')
        elif symbol == 'ISO_Level5_Latch':
            self.prepare_for_retag_entry()
            self.widget.reappear()
        else:
            self.resolve_symbol(symbol)

    def hide_and_reset(self):
        self._self_reset()
        i3.mode_default()

    def list_sublist(self, position, option_list):
        self.widget.clear()
        self.widget.add_label(option_list[0][0][:position])
        for option in option_list:
            self.widget.add_label(f' {option[0][position:]}')
        self.widget.adjustSize()

    def resolve_symbol(self, symbol):
        if self.position == 0:
            if self.workspace_mode:
                tags.switch_to_tag(symbol)
                return
            else:
                self.widget.reappear()
                self.sublist = file_handler.get_command_list(
                    i3.cache.current_workspace,
                    i3.cache.focused_window)

        if symbol == 'space': symbol = '_'
        elif symbol == 'minus': symbol = '_'
        elif symbol == 'period': symbol = '.'

        sublist = [x for x in self.sublist if x[0][self.position] == symbol]
        sublist_len = len(sublist)

        if sublist_len == 0:
            return
        elif sublist_len == 1:
            launcher.fork(sublist[0][1])
        else:
            step = 1
            while len(set([x[0][self.position+step] for x in sublist])) == 1:
                step += 1
            self.position += step
            self.sublist = sublist
            gui.list_sublist(self.position, self.sublist)

    def _prepare_position(self):
        self.widget.move_(i3.cache.focused_window.rect.x,
                          i3.cache.focused_window.rect.y + 75)

    def _prepare_tags(self):
        for tag in tags.tag_tree.object_list():
            windows = tag.leaves()
            if not windows:
                try:
                    windows = tag.floating_nodes[0].nodes
                except IndexError:  # no widows at all, label tag name
                    self.widget.add_label(f'''{tag.name} 
''')
            for window in windows:
                self.label_i3_window(tag, window)

    def label_i3_window(self, tag, window):
        if tag.name in ['f', 'j', 'q']:
            color = 'grey'
        elif tag.name == 'hidden':
            return
        else:
            color = None
        self.widget.add_label(f'''{tag.name}           {window.window_class}
{window.name}''',
                              window.focused,
                              not window.urgent, color)


class Tags:
    def __init__(self):
        self.tag_tree = i3.get_tree()
        self.previous_tag_name = i3.cache.current_workspace.name

    def get_names(self):
        return [x.name for x in self.object_list]

    @property
    def object_list(self):
        return self.tag_tree.nodes[1].nodes[1].nodes

    @object_list.setter
    def object_list(self, list_):
        self.tag_tree.nodes[1].nodes[1].nodes = list_

    @Slot()
    def process_retag_entry(self, entry):
        if entry == 'exit':
            app.exit()
        elif entry == '':
            i3.command(f'[con_id={i3.cache.focused_window.id}] kill')
            gui.hide_and_reset()
            return
        else:
            print(entry)
            entry_list = [x for x in entry]
            try:
                entry_list.remove('.')
            except ValueError:
                flag_move = False
            else:
                flag_move = True
            print(entry_list)
            self.remove_window_from_all_tags()
            self.add_window_to_tags(entry_list)
            self.tidy_current_workspace(entry_list)
            if flag_move:
                self.switch_to_tag(entry_list[0])
            else:
                gui.hide_and_reset()

    def remove_window_from_all_tags(self):
        # remove current window from current positions in tag tree
        self.tag_tree.remove_nodes_by_id(i3.cache.focused_window.id)

    def add_window_to_tags(self, entry_list):
        for char in entry_list:
            if char in self.get_names():
                self.add_window_to_existing_tag(char)
            else:
                new_tag = i3.get_new_workspace_container()
                new_tag.name = char
                new_tag.nodes = [i3.cache.focused_window]
                self.object_list.append(new_tag)

    def tidy_current_workspace(self, entry_list):
        if i3.cache.current_workspace.name not in entry_list:
            i3.command(
                f'[con_id={i3.cache.focused_window.id}] move window to workspace {entry_list[0]}')

    def branch_tag(self, binding_event):
        tag_name = binding_event.binding.symbol
        current_tag = self.tag_tree.find_focused().tag()
        # new_tag = copy.copy(current_tag)
        new_tag = None
        new_tag.name = tag_name
        self.object_list.append(new_tag)
        i3.command(f'move window to workspace {tag_name}')

    # @multipledispatch.dispatch(object)
    # def switch_tag(self, binding_event):
    #    self.switch_to_tag(binding_event.binding.symbol)

    # @multipledispatch.dispatch(str)
    def switch_to_tag(self, symbol):
        target_name = self.find_target_workspace_name(symbol)
        target_workspace = i3.cache.tree.find_tag_by_name(target_name)
        target_tag = self.tag_tree.find_tag_by_name(target_name)
        if target_tag:
            for i, window in enumerate(target_tag.nodes):
                try:
                    if window.id == target_workspace.nodes[i].id:
                        continue
                except (IndexError, AttributeError):
                    pass
                # if anything goes wrong with the window being in
                # workspace on correct position
                self._reload_window_to_workspace(window, symbol)
        # Pycharm will not let execute
        # i3.commnand(f'workspace {char}')
        self.previous_tag_name = i3.cache.current_workspace.name
        subprocess.run(['i3-msg', 'workspace', target_name])
        gui.hide_and_reset()

    def find_target_workspace_name(self, symbol):
        if i3.cache.current_workspace.name == symbol:
            target = self.previous_tag_name
        else:
            target = symbol
        return target

    def _reload_window_to_workspace(self, window, target_name):
        # if you uncomment the next code line you get stable window
        # positions in
        # tagged workspaces, but modified layout will be impossible
        # to keep. i3tags will reset them.
        # i3.command(f'[con_id={window.id}]move window to workspace tmp')
        i3.command(f'[con_id={window.id}] move window to workspace {target_name}')

    def update(self):
        self._inspect_tag_tree()
        self._inspect_workspaces()
        self._inspect_windows()
        self.object_list.sort(key=lambda x: x.name)

    def add_window_to_existing_tag(self, char):
        for tag in self.object_list:
            if char == tag.name:
                tag.nodes.append(i3.cache.focused_window)
                return

    def retitle_focused_window(self, title):
        focused_window = self.tag_tree.find_focused()
        for window in self.tag_tree.leaves():
            if focused_window.id == window.id:
                window.name = title
                window.window_title = title
        subprocess.run(['xdotool',
                        'set_window',
                        '--name',
                        title,
                        str(self.tag_tree.find_focused().window)
                        ])

    def _inspect_tag_tree(self):
        current_workspace = i3.cache.current_workspace
        tags_ = [
                current_workspace if current_workspace.name == tag.name else
                tag.update_tag(i3.cache.tree)
                for tag in self.object_list
                    ]
        self.object_list = [tag for tag in tags_ if tag.nodes]

    def _inspect_workspaces(self):
        for workspace in i3.cache.workspaces:
            if workspace.name not in self.get_names():
                self.object_list.append(workspace)

    def _inspect_windows(self):
        tagged_window_ids = [window.id for window in self.tag_tree.leaves()]
        for window in i3.cache.tree.leaves():
            if window.id not in tagged_window_ids:
                # copy window from workspace to tag
                workspace = (i3.cache.tree
                               .find_by_id(window.id)
                               .workspace())
                try:
                    self.tag_tree.find_by_id(workspace.id).nodes.append(window)
                except AttributeError:
                    logging.debug([workspace.id])
                    logging.debug([workspace.id for workspace in i3.cache.tree.workspaces()])
                    logging.debug(workspace.id in [workspace.id for workspace in i3.cache.tree.workspaces()])



i3 = i3ipc_interface.i3
tags = Tags()
if __name__ == "__main__":
    launcher = Launcher()
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication()
    gui = GUI()
    i3ipc_interface.signals.binding.connect(gui.handle_binding)
    gui.widget.submit_retag_entry.connect(tags.process_retag_entry)
    app.exec_()
    # this will run after app.exit()
    i3.main_quit()

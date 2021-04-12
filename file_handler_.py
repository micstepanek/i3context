import os
import yaml


def get_command_list(workspace_object, focused_container):
    final_list = _get_bin_list()
    final_list.extend(_get_workspace_bin_list(workspace_object))
    if focused_container.window_class:
        final_list.extend(_get_class_bin_list(focused_container))
        final_list.extend(_get_move_bin_list(workspace_object, focused_container))
    final_list.sort(key=lambda x: x[0])
    return final_list


def _get_bin_list():
    list_to_return = []
    for bin in config['bins']:
        simple_list = _list_dir(bin)
        list_to_return.extend([[x, x] for x in simple_list])
    return list_to_return

def _get_workspace_bin_list(workspace_object):
    path = os.path.join(config['workspace_bins'], workspace_object.name)
    try:
        simple_list = _list_dir(path)
    except FileNotFoundError:
        return []
    else:
        pair_list = [[x, os.path.join(path, x)] for x in simple_list]
        return pair_list


def _get_class_bin_list(focused_window):
    path = os.path.join(config['class_bins'], focused_window.window_class)
    try:
        simple_list = _list_dir(path)
    except FileNotFoundError:
        return []
    else:
        pair_list = [[x, os.path.join(path, x)] for x in simple_list]
        return pair_list


def _get_move_bin_list(workspace_object, focused_window):
    if len(workspace_object.nodes) > 1 or \
           focused_window in workspace_object.floating_nodes:
        path = config['move_bin']
        simple_list = _list_dir(path)
        pair_list = [[x, os.path.join(path, x)] for x in simple_list]
        return pair_list
    return []


def _list_dir(folder):
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    commands = [c for c in files if '.' not in c[-4:-2]]
    try:
        commands.remove('.gitignore')
    except ValueError:
        pass
    return commands


with open('/config.yml', 'r') as file:
    config = yaml.safe_load(file)

#!/usr/bin/env python3
"""
Automated test for examples/list/list_actions using AT-SPI2.

Verifies:
1. Window appears with a list containing 3 items
2. First item is selected by default
3. Disable button disables the list
4. Enable button re-enables the list
5. Removeselected removes the selected item
6. Clear button clears all items
7. Refresh reloads items from file
8. Cancel closes the dialog
"""

import subprocess
import sys
import time
import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi

sys.path.insert(0, sys.path[0] + '/..')
from testlib import TestRunner

TIMEOUT = 10  # seconds


def wait_for_window(name_substring, timeout=TIMEOUT):
    """Wait for a window matching the name to appear in AT-SPI tree."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        desktop = Atspi.get_desktop(0)
        for i in range(desktop.get_child_count()):
            app = desktop.get_child_at_index(i)
            if app is None:
                continue
            for j in range(app.get_child_count()):
                win = app.get_child_at_index(j)
                if win and name_substring.lower() in (win.get_name() or '').lower():
                    return app, win
        time.sleep(0.3)
    return None, None


def find_widgets(node, role=None):
    """Recursively find all widgets, optionally filtered by role."""
    results = []
    if node is None:
        return results
    try:
        node_role = node.get_role()
    except Exception:
        return results
    if role is None or node_role == role:
        results.append(node)
    for i in range(node.get_child_count()):
        results.extend(find_widgets(node.get_child_at_index(i), role))
    return results


def find_button(window, label_text):
    """Find a push button by its label text."""
    for btn in find_widgets(window, Atspi.Role.PUSH_BUTTON):
        name = (btn.get_name() or '').lower()
        if label_text.lower() == name:
            return btn
    return None


def do_action(widget, action_name=''):
    """Invoke an action on a widget."""
    ai = widget.get_action_iface()
    if ai is None:
        return False
    for i in range(ai.get_n_actions()):
        if action_name == '' or ai.get_action_name(i) == action_name:
            ai.do_action(i)
            return True
    return False


def is_enabled(widget):
    """Check if a widget is sensitive/enabled."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.SENSITIVE)


def is_selected(widget):
    """Check if a widget is selected."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.SELECTED)


def get_table_cells(window):
    """Get all table cell widgets (list items)."""
    return find_widgets(window, Atspi.Role.TABLE_CELL)


def dump_tree(node, indent=0):
    """Debug helper: print the AT-SPI widget tree."""
    if node is None:
        return
    try:
        role = node.get_role_name()
        name = node.get_name() or ''
        states = node.get_state_set()
        enabled = states.contains(Atspi.StateType.ENABLED)
        print(f"{'  ' * indent}{role}: '{name}' enabled={enabled}")
    except Exception as e:
        print(f"{'  ' * indent}(error: {e})")
        return
    for i in range(node.get_child_count()):
        dump_tree(node.get_child_at_index(i), indent + 1)


t = TestRunner()

# Kill any leftover gtkdialog3 processes
subprocess.run(['pkill', '-x', 'gtkdialog3'], capture_output=True)
time.sleep(0.5)

# Launch the example
t.log("Launching list_actions example...")
proc = subprocess.Popen(
    ['./examples/list/list_actions'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('gtkdialog3')

if window is None:
    proc.kill()
    t.abort("Could not find gtkdialog3 window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")
if t.verbose:
    print()
    print("Widget tree:")
    dump_tree(window)
    print()

# --- Test 1: Initial list contents ---
t.begin("testInitialContents")
cells = get_table_cells(window)
cell_names = [c.get_name() or '' for c in cells]
expected = ['First item', 'Second item', 'Third item']
t.check(cell_names == expected,
        f"List has 3 items: {cell_names}"
        if cell_names == expected
        else f"Expected {expected}, got {cell_names}")

# --- Test 2: First item is selected by default ---
t.begin("testDefaultSelection")
t.check(cells and is_selected(cells[0]),
        "First item is selected")

# --- Test 3: Disable button disables the list ---
t.begin("testDisableList")
disable_btn = find_button(window, 'Disable')
if disable_btn:
    do_action(disable_btn, 'click')
    time.sleep(0.5)
    tables = find_widgets(window, Atspi.Role.TABLE)
    t.check(tables and not is_enabled(tables[0]),
            "List is disabled")
else:
    t.check(False, "Disable button not found")

# --- Test 4: Enable button re-enables the list ---
t.begin("testEnableList")
enable_btn = find_button(window, 'Enable')
if enable_btn:
    do_action(enable_btn, 'click')
    time.sleep(0.5)
    tables = find_widgets(window, Atspi.Role.TABLE)
    t.check(tables and is_enabled(tables[0]),
            "List is enabled again")
else:
    t.check(False, "Enable button not found")

# --- Test 5: Removeselected removes the selected item ---
t.begin("testRemoveSelected")
remove_btn = find_button(window, 'Removeselected')
if remove_btn:
    do_action(remove_btn, 'click')
    time.sleep(0.5)
    cells = get_table_cells(window)
    cell_names = [c.get_name() or '' for c in cells]
    t.check('First item' not in cell_names and len(cell_names) == 2,
            f"Selected item removed, remaining: {cell_names}"
            if 'First item' not in cell_names and len(cell_names) == 2
            else f"Expected 2 items without 'First item', got {cell_names}")
else:
    t.check(False, "Removeselected button not found")

# --- Test 6: Clear button clears all items ---
t.begin("testClearList")
clear_btn = find_button(window, 'Clear')
if clear_btn:
    do_action(clear_btn, 'click')
    time.sleep(0.5)
    cells = get_table_cells(window)
    if len(cells) == 0:
        t.check(True, "List is empty after Clear")
    else:
        cell_names = [c.get_name() or '' for c in cells]
        t.check(False, f"List should be empty after Clear, got {cell_names}")
else:
    t.check(False, "Clear button not found")

# --- Test 7: Refresh reloads items from file ---
t.begin("testRefreshList")
refresh_btn = find_button(window, 'Refresh')
if refresh_btn:
    do_action(refresh_btn, 'click')
    time.sleep(0.5)
    cells = get_table_cells(window)
    cell_names = [c.get_name() or '' for c in cells]
    t.check(cell_names == expected,
            f"Items reloaded: {cell_names}"
            if cell_names == expected
            else f"Expected {expected} after Refresh, got {cell_names}")
else:
    t.check(False, "Refresh button not found")

# --- Test 8: Cancel closes the dialog ---
t.begin("testCancelClose")
cancel_btn = find_button(window, 'Cancel')
if cancel_btn:
    do_action(cancel_btn, 'click')
    time.sleep(1)
    retcode = proc.poll()
    if t.check(retcode is not None,
               f"Dialog closed after Cancel (exit code {retcode})"
               if retcode is not None
               else "Dialog should have closed after Cancel"):
        pass
    else:
        proc.kill()
        proc.wait()
else:
    t.check(False, "Cancel button not found")
    proc.kill()
    proc.wait()

t.summary()

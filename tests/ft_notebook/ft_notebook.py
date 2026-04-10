#!/usr/bin/env python3
"""
Automated test for examples/notebook/notebook using AT-SPI2.

Launches the notebook example dialog and verifies:
1. The window appears with a notebook containing three tabs
2. Checkbox tab: three checkboxes, all unchecked, toggleable
3. Radiobutton tab: three radiobuttons, third selected by default
4. Tree tab: tree table with data rows loaded from file
5. Clicking OK closes the dialog
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
            app_name = (app.get_name() or '').lower()
            if 'gtkdialog' not in app_name:
                continue
            for j in range(app.get_child_count()):
                win = app.get_child_at_index(j)
                if win and name_substring.lower() in (win.get_name() or '').lower():
                    return app, win
        time.sleep(0.3)
    return None, None


def find_widgets(node, role=None, depth=0):
    """Recursively find all widgets, optionally filtered by role."""
    results = []
    if node is None:
        return results
    try:
        node_role = node.get_role()
        node_name = node.get_name() or ''
    except Exception:
        return results

    if role is None or node_role == role:
        results.append(node)

    for i in range(node.get_child_count()):
        child = node.get_child_at_index(i)
        results.extend(find_widgets(child, role, depth + 1))
    return results


def dump_tree(node, indent=0):
    """Debug helper: print the AT-SPI widget tree."""
    if node is None:
        return
    try:
        role = node.get_role_name()
        name = node.get_name() or ''
        states = node.get_state_set()
        selected = states.contains(Atspi.StateType.SELECTED)
        checked = states.contains(Atspi.StateType.CHECKED)
        print(f"{'  ' * indent}{role}: '{name}' checked={checked} selected={selected}")
    except Exception as e:
        print(f"{'  ' * indent}(error: {e})")
        return
    for i in range(node.get_child_count()):
        dump_tree(node.get_child_at_index(i), indent + 1)


def do_action(widget, action_name=''):
    """Invoke an action on a widget (e.g. 'click')."""
    ai = widget.get_action_iface()
    if ai is None:
        return False
    for i in range(ai.get_n_actions()):
        if action_name == '' or ai.get_action_name(i) == action_name:
            ai.do_action(i)
            return True
    return False


def is_checked(widget):
    """Check if a checkbox/radiobutton is checked."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.CHECKED)


def is_selected(widget):
    """Check if a widget is selected."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.SELECTED)


def is_showing(widget):
    """Check if a widget is currently showing on screen."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.SHOWING)


def select_tab(tab_list, index):
    """Select a tab by index using the selection interface."""
    si = tab_list.get_selection_iface()
    if si:
        si.select_child(index)
        return True
    return False


t = TestRunner()

# Launch the notebook example
t.log("Launching notebook example...")
proc = subprocess.Popen(
    ['./examples/notebook/notebook'],
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

# --- Test 1: Initial state - notebook with 3 tabs ---
t.begin("testInitialState")

tab_lists = find_widgets(window, Atspi.Role.PAGE_TAB_LIST)
tabs = find_widgets(window, Atspi.Role.PAGE_TAB)
t.check(len(tabs) == 3, f"Found 3 notebook tabs (got {len(tabs)})")
tab_list = tab_lists[0] if tab_lists else None

if len(tabs) >= 3:
    t.check(tabs[0].get_name() == 'Checkbox', f"Tab 1 is 'Checkbox' (got '{tabs[0].get_name()}')")
    t.check(tabs[1].get_name() == 'Radiobutton', f"Tab 2 is 'Radiobutton' (got '{tabs[1].get_name()}')")
    t.check(tabs[2].get_name() == 'Tree', f"Tab 3 is 'Tree' (got '{tabs[2].get_name()}')")
    t.check(is_selected(tabs[0]), "Checkbox tab is selected initially")

buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
button_names = [b.get_name() for b in buttons]
t.check('Cancel' in button_names, "Cancel button found")
t.check('OK' in button_names, "OK button found")

t.screenshot("gtkdialog3")

# --- Test 2: Checkbox tab - verify and toggle ---
t.begin("testCheckboxTab")

checkboxes = find_widgets(window, Atspi.Role.CHECK_BOX)
t.check(len(checkboxes) == 3, f"Found 3 checkboxes (got {len(checkboxes)})")

if len(checkboxes) >= 3:
    t.check(checkboxes[0].get_name() == 'This is a checkbox',
            f"Checkbox 1 label correct (got '{checkboxes[0].get_name()}')")
    for i, cb in enumerate(checkboxes):
        t.check(not is_checked(cb), f"Checkbox {i+1} is unchecked initially")

    # Toggle first checkbox
    do_action(checkboxes[0], 'click')
    time.sleep(0.5)
    t.check(is_checked(checkboxes[0]), "Checkbox 1 is checked after click")

    # Toggle back
    do_action(checkboxes[0], 'click')
    time.sleep(0.5)
    t.check(not is_checked(checkboxes[0]), "Checkbox 1 unchecked after second click")

# --- Test 3: Switch to Radiobutton tab ---
t.begin("testRadiobuttonTab")

if len(tabs) >= 2 and tab_list:
    select_tab(tab_list, 1)
    time.sleep(0.5)

    t.check(is_selected(tabs[1]), "Radiobutton tab is now selected")

    radiobuttons = find_widgets(window, Atspi.Role.RADIO_BUTTON)
    t.check(len(radiobuttons) == 3, f"Found 3 radiobuttons (got {len(radiobuttons)})")

    if len(radiobuttons) >= 3:
        t.check(radiobuttons[2].get_name() == 'Third radiobutton',
                f"Radiobutton 3 label correct (got '{radiobuttons[2].get_name()}')")
        t.check(not is_checked(radiobuttons[0]), "Radiobutton 1 is not selected")
        t.check(not is_checked(radiobuttons[1]), "Radiobutton 2 is not selected")
        t.check(is_checked(radiobuttons[2]), "Radiobutton 3 is selected (default=true)")

        # Click radiobutton 1 and verify it becomes selected
        do_action(radiobuttons[0], 'click')
        time.sleep(0.5)
        t.check(is_checked(radiobuttons[0]), "Radiobutton 1 selected after click")
        t.check(not is_checked(radiobuttons[2]), "Radiobutton 3 deselected after clicking 1")

# --- Test 4: Switch to Tree tab ---
t.begin("testTreeTab")

if len(tabs) >= 3 and tab_list:
    select_tab(tab_list, 2)
    time.sleep(0.5)

    t.check(is_selected(tabs[2]), "Tree tab is now selected")

    tables = find_widgets(window, Atspi.Role.TREE_TABLE)
    t.check(len(tables) >= 1, f"Found tree table widget (got {len(tables)})")

    if tables:
        cells = find_widgets(tables[0], Atspi.Role.TABLE_CELL)
        t.check(len(cells) > 0, f"Tree has data rows (got {len(cells)} cells)")

# --- Test 5: Close via OK button ---
t.begin("testCloseDialog")

ok_button = None
for b in buttons:
    if b.get_name() == 'OK':
        ok_button = b
        break

if t.check(ok_button is not None, "OK button found"):
    do_action(ok_button, 'click')
    time.sleep(1)

    retcode = proc.poll()
    if not t.check(retcode is not None,
                   f"Dialog closed after OK click (exit code {retcode})"
                   if retcode is not None
                   else "Dialog should have closed after OK click"):
        proc.kill()
else:
    proc.kill()

t.summary()

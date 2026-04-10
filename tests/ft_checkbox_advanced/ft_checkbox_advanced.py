#!/usr/bin/env python3
"""
Automated test for examples/checkbox/checkbox_advanced using AT-SPI2.

Launches the checkbox_advanced example dialog and verifies:
1. Initial states of all 6 checkboxes
2. Toggling chk0 enables/disables the File menu
3. Disable/Enable buttons control chk0
4. chk2 (active=false) and chk3 (active=true) initial states
5. chk5 starts in indeterminate state
6. Closing via File > Quit
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


def wait_for_window(name, pid=None, timeout=TIMEOUT):
    """Wait for a window matching the name to appear in AT-SPI tree.
    If pid is given, also match the application's process ID."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        desktop = Atspi.get_desktop(0)
        for i in range(desktop.get_child_count()):
            app = desktop.get_child_at_index(i)
            if app is None:
                continue
            if pid is not None:
                try:
                    if app.get_process_id() != pid:
                        continue
                except Exception:
                    continue
            for j in range(app.get_child_count()):
                win = app.get_child_at_index(j)
                if win and (win.get_name() or '') == name:
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
        child = node.get_child_at_index(i)
        results.extend(find_widgets(child, role))
    return results


def find_widget_by_name(node, role, name):
    """Find a widget by role and name."""
    for w in find_widgets(node, role):
        if (w.get_name() or '') == name:
            return w
    return None


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


def is_sensitive(widget):
    """Check if a widget is sensitive/enabled."""
    return widget.get_state_set().contains(Atspi.StateType.SENSITIVE)


def is_checked(widget):
    """Check if a checkbox is checked."""
    return widget.get_state_set().contains(Atspi.StateType.CHECKED)


def is_indeterminate(widget):
    """Check if a checkbox is in indeterminate state."""
    return widget.get_state_set().contains(Atspi.StateType.INDETERMINATE)


t = TestRunner()

# Launch the example
t.log("Launching checkbox_advanced example...")
proc = subprocess.Popen(
    ['./examples/checkbox/checkbox_advanced'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('CheckBox Advanced')
t.screenshot('CheckBox Advanced')

if window is None:
    proc.kill()
    t.abort("Could not find 'CheckBox Advanced' window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")

# Gather widgets
checkboxes = find_widgets(window, Atspi.Role.CHECK_BOX)
buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
menus = find_widgets(window, Atspi.Role.MENU)
menu_items = find_widgets(window, Atspi.Role.MENU_ITEM)

t.log(f"Found {len(checkboxes)} checkboxes, {len(buttons)} buttons, "
      f"{len(menus)} menus, {len(menu_items)} menu items")

if len(checkboxes) < 6:
    proc.kill()
    t.abort(f"Expected 6 checkboxes, found {len(checkboxes)}")

chk0 = checkboxes[0]  # Enable/disable the File menu
chk1 = checkboxes[1]  # Enable/disable (block-function-signals)
chk2 = checkboxes[2]  # Initially active=false
chk3 = checkboxes[3]  # Initially active=true
chk4 = checkboxes[4]  # draw-indicator=false
chk5 = checkboxes[5]  # inconsistent=true

# Find File menu
file_menu = find_widget_by_name(window, Atspi.Role.MENU, 'File')

# Find buttons by name in order (first 4 belong to chk0, next 4 to chk1)
btn_disable_0 = buttons[0]
btn_enable_0 = buttons[1]

# --- Test 1: Initial states ---
t.begin("testInitialStates")
t.check(is_checked(chk0), "chk0 is checked (input echoes true)")
t.check(is_checked(chk1), "chk1 is checked (input echoes true)")
t.check(not is_checked(chk2), "chk2 is unchecked (active=false)")
t.check(is_checked(chk3), "chk3 is checked (active=true)")
t.check(not is_checked(chk4), "chk4 is unchecked (draw-indicator=false)")
t.check(is_indeterminate(chk5), "chk5 is indeterminate (inconsistent=true)")

# --- Test 2: File menu is sensitive initially ---
t.begin("testFileMenuInitial")
t.check(file_menu and is_sensitive(file_menu),
        "File menu is sensitive (chk0 is checked)")

# --- Test 3: Uncheck chk0 -> File menu should become insensitive ---
t.begin("testUncheckChk0")
do_action(chk0, 'click')
time.sleep(0.5)

t.check(not is_checked(chk0), "chk0 is now unchecked")
t.check(file_menu and not is_sensitive(file_menu),
        "File menu is now insensitive")

# --- Test 4: Re-check chk0 -> File menu sensitive again ---
t.begin("testRecheckChk0")
do_action(chk0, 'click')
time.sleep(0.5)

t.check(is_checked(chk0), "chk0 is checked again")
t.check(file_menu and is_sensitive(file_menu),
        "File menu is sensitive again")

# --- Test 5: Disable button makes chk0 insensitive ---
t.begin("testDisableButton")
do_action(btn_disable_0, 'click')
time.sleep(0.5)

t.check(not is_sensitive(chk0),
        "chk0 is insensitive after Disable button")

# --- Test 6: Enable button makes chk0 sensitive again ---
t.begin("testEnableButton")
do_action(btn_enable_0, 'click')
time.sleep(0.5)

t.check(is_sensitive(chk0),
        "chk0 is sensitive after Enable button")

# --- Test 7: Toggle chk2 and chk3 ---
t.begin("testToggleChk2Chk3")
do_action(chk2, 'click')
time.sleep(0.3)

t.check(is_checked(chk2), "chk2 is now checked after click")

do_action(chk3, 'click')
time.sleep(0.3)

t.check(not is_checked(chk3), "chk3 is now unchecked after click")

# --- Test 8: Close via File > Quit ---
t.begin("testFileQuit")
if file_menu:
    do_action(file_menu, 'click')
    time.sleep(0.5)
    quit_item = find_widget_by_name(window, Atspi.Role.MENU_ITEM, 'Quit')
    if quit_item:
        do_action(quit_item, 'click')
        time.sleep(1)

        retcode = proc.poll()
        if t.check(retcode is not None,
                   f"Dialog closed via Quit (exit code {retcode})"
                   if retcode is not None
                   else "Dialog should have closed after Quit"):
            pass
        else:
            proc.kill()
    else:
        t.check(False, "Could not find Quit menu item")
        proc.kill()
else:
    t.check(False, "Could not find File menu")
    proc.kill()

t.summary()

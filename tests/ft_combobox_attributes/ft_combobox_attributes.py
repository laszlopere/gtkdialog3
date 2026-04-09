#!/usr/bin/env python3
"""
Automated test for examples/combobox/combobox_attributes using AT-SPI2.

Verifies:
1. The window appears with the expected widgets
2. Two combo boxes are present with three items each
3. Selecting values from the combo boxes works
4. Clicking OK closes the dialog and prints the selected values
"""

import subprocess
import sys
import time
import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi

sys.path.insert(0, sys.path[0] + '/..')
from testlib import TestRunner

TIMEOUT = 10


def wait_for_window(timeout=TIMEOUT):
    """Wait for a gtkdialog3 window to appear in AT-SPI tree."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        desktop = Atspi.get_desktop(0)
        for i in range(desktop.get_child_count()):
            app = desktop.get_child_at_index(i)
            if app is None:
                continue
            if 'gtkdialog' not in (app.get_name() or '').lower():
                continue
            for j in range(app.get_child_count()):
                win = app.get_child_at_index(j)
                if win:
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


t = TestRunner()

# Launch the example
t.log("Launching combobox_attributes example...")
proc = subprocess.Popen(
    ['./examples/combobox/combobox_attributes'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window()

if window is None:
    proc.kill()
    t.abort("Could not find gtkdialog3 window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")

# --- Test 1: Widget presence ---
t.begin("testWidgetPresence")
combos = find_widgets(window, Atspi.Role.COMBO_BOX)
t.check(len(combos) == 2, f"Found 2 combo boxes (got {len(combos)})")

labels = find_widgets(window, Atspi.Role.LABEL)
label_names = [l.get_name() or '' for l in labels]
t.check(any('value-in-list' in n for n in label_names),
        "value-in-list label is present")
t.check(any('allow-empty' in n for n in label_names),
        "allow-empty label is present")

buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
button_names = [(b.get_name() or '').lower() for b in buttons]
t.check(any('ok' in n for n in button_names), "OK button is present")
t.check(any('cancel' in n for n in button_names), "Cancel button is present")

# --- Test 2: Combo box items ---
t.begin("testComboItems")
if len(combos) >= 2:
    items1 = find_widgets(combos[0], Atspi.Role.MENU_ITEM)
    item_names1 = [mi.get_name() or '' for mi in items1]
    t.check(len(items1) == 3, f"First combo has 3 items (got {len(items1)})")
    t.check(item_names1 == ['First', 'Second', 'Third'],
            f"First combo items are First/Second/Third (got {item_names1})")

    items2 = find_widgets(combos[1], Atspi.Role.MENU_ITEM)
    item_names2 = [mi.get_name() or '' for mi in items2]
    t.check(len(items2) == 3, f"Second combo has 3 items (got {len(items2)})")
    t.check(item_names2 == ['First', 'Second', 'Third'],
            f"Second combo items are First/Second/Third (got {item_names2})")

# --- Test 3: Select values and check output ---
t.begin("testSelectAndOutput")
if len(combos) >= 2:
    # Select "Second" from first combobox
    items1 = find_widgets(combos[0], Atspi.Role.MENU_ITEM)
    t.check(do_action(items1[1], 'click'),
            "Clicked 'Second' in first combo box")
    time.sleep(0.5)

    # Select "Third" from second combobox
    items2 = find_widgets(combos[1], Atspi.Role.MENU_ITEM)
    t.check(do_action(items2[2], 'click'),
            "Clicked 'Third' in second combo box")
    time.sleep(0.5)

    # Click OK to close
    ok_button = None
    for b in buttons:
        if 'ok' in (b.get_name() or '').lower():
            ok_button = b
            break

    if ok_button:
        do_action(ok_button, 'click')
        time.sleep(1)

        retcode = proc.poll()
        if t.check(retcode is not None,
                   f"Dialog closed after OK click (exit code {retcode})"
                   if retcode is not None
                   else "Dialog should have closed after OK click"):
            stdout = proc.stdout.read().decode()
            t.log(f"stdout: {repr(stdout)}")
            t.check('COMBOBOX1="Second"' in stdout,
                    "COMBOBOX1 is 'Second' in output")
            t.check('COMBOBOX2="Third"' in stdout,
                    "COMBOBOX2 is 'Third' in output")
            t.check('EXIT="OK"' in stdout,
                    "EXIT is 'OK' in output")
        else:
            proc.kill()
    else:
        t.check(False, "OK button not found")
        proc.kill()

t.summary()

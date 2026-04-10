#!/usr/bin/env python3
"""
Automated test for examples/radiobutton/radiobutton using AT-SPI2.

Verifies:
1. Window appears with expected title
2. Description label contains multi-line text
3. Four radio buttons are present with correct labels
4. First radio button is selected by default
5. Clicking another radio button deselects the first
6. Buttonbox contains OK and Cancel stock buttons
7. Cancel closes the dialog
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


def wait_for_window(name_substring, timeout=TIMEOUT, app_name='gtkdialog3'):
    """Wait for a window matching the name to appear in AT-SPI tree."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        desktop = Atspi.get_desktop(0)
        for i in range(desktop.get_child_count()):
            app = desktop.get_child_at_index(i)
            if app is None:
                continue
            if app_name and app_name.lower() not in (app.get_name() or '').lower():
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


def is_checked(widget):
    """Check if a radio button is checked."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.CHECKED)


def dump_tree(node, indent=0):
    """Debug helper: print the AT-SPI widget tree."""
    if node is None:
        return
    try:
        role = node.get_role_name()
        name = node.get_name() or ''
        states = node.get_state_set()
        checked = states.contains(Atspi.StateType.CHECKED)
        print(f"{'  ' * indent}{role}: '{name}' checked={checked}")
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
t.log("Launching radiobutton example...")
proc = subprocess.Popen(
    ['./examples/standard/radiobutton'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('Configuration File Changed')
t.screenshot('Configuration File Changed')

if window is None:
    proc.kill()
    t.abort("Could not find window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")
if t.verbose:
    print()
    print("Widget tree:")
    dump_tree(window)
    print()

# --- Test 1: Window title ---
t.begin("testWindowTitle")
t.check('Configuration File Changed' in (window.get_name() or ''),
        "Window title contains 'Configuration File Changed'")

# --- Test 2: Multi-line description label ---
t.begin("testDescriptionLabel")
labels = find_widgets(window, Atspi.Role.LABEL)
desc_label = None
for lbl in labels:
    name = lbl.get_name() or ''
    if 'configuration file' in name.lower():
        desc_label = lbl
        break
if desc_label:
    text = desc_label.get_name()
    t.check('\n' in text,
            "Description label contains newlines (multi-line)")
    t.check('package maintainer' in text,
            "Description mentions 'package maintainer'")
    t.check('modified' in text,
            "Description mentions 'modified'")
else:
    t.check(False, "Description label not found")

# --- Test 3: Four radio buttons present ---
t.begin("testRadioButtons")
radios = find_widgets(window, Atspi.Role.RADIO_BUTTON)
t.check(len(radios) == 4,
        f"Found 4 radio buttons"
        if len(radios) == 4
        else f"Expected 4 radio buttons, found {len(radios)}")

if len(radios) == 4:
    radio_names = [r.get_name() or '' for r in radios]
    t.check('Keep' in radio_names[0],
            f"First radio: '{radio_names[0]}'")
    t.check('maintainer' in radio_names[1],
            f"Second radio: '{radio_names[1]}'")
    t.check('differences' in radio_names[2],
            f"Third radio: '{radio_names[2]}'")
    t.check('shell' in radio_names[3].lower(),
            f"Fourth radio: '{radio_names[3]}'")

# --- Test 4: First radio button selected by default ---
t.begin("testDefaultSelection")
if len(radios) >= 1:
    t.check(is_checked(radios[0]),
            "First radio button is selected by default")
    t.check(not is_checked(radios[1]),
            "Second radio button is not selected")

# --- Test 5: Clicking another radio deselects the first ---
t.begin("testRadioToggle")
if len(radios) >= 2:
    do_action(radios[2], 'click')
    time.sleep(0.5)
    t.check(not is_checked(radios[0]),
            "First radio is now deselected")
    t.check(is_checked(radios[2]),
            "Third radio is now selected")

# --- Test 6: Stock buttons present ---
t.begin("testStockButtons")
buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
button_names = [(b.get_name() or '').lower() for b in buttons]
t.log(f"Buttons found: {button_names}")
t.check(any('ok' in n for n in button_names),
        "OK button present")
t.check(any('cancel' in n for n in button_names),
        "Cancel button present")

# --- Test 7: Cancel closes the dialog ---
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

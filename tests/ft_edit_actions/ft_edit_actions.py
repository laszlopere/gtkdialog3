#!/usr/bin/env python3
"""
Automated test for examples/edit/edit_actions using AT-SPI2.

Verifies:
1. Window appears with expected widgets
2. Editor is loaded with text from input file
3. Select All + Cut empties the editor
4. Paste restores the text from clipboard
5. Clear empties the editor
6. Refresh reloads text from input file
7. Disable/Enable toggles sensitivity
8. OK button closes dialog and prints action IDs
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


def wait_for_window(title_substring, timeout=TIMEOUT):
    """Wait for a gtkdialog3 window with matching title."""
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
                if win and title_substring.lower() in (win.get_name() or '').lower():
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


def find_button(buttons, name):
    """Find a button by its label."""
    for b in buttons:
        if (b.get_name() or '') == name:
            return b
    return None


def get_editor_text(editor):
    """Get all text from the editor widget."""
    return Atspi.Text.get_text(editor, 0, -1)


t = TestRunner()

# Launch the example
t.log("Launching edit_actions example...")
proc = subprocess.Popen(
    ['./examples/edit/edit_actions'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1.5)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('Edit Actions')
t.screenshot('Edit Actions')

if window is None:
    proc.kill()
    t.abort("Could not find Edit Actions window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")

# Gather widgets
editors = find_widgets(window, Atspi.Role.TEXT)
buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
panels = find_widgets(window, Atspi.Role.PANEL)
t.log(f"Found {len(editors)} text widgets, {len(buttons)} buttons")

# --- Test 1: Widget presence ---
t.begin("testWidgetPresence")
t.check('Edit Actions' in (window.get_name() or ''),
        "Window title is 'Edit Actions'")
t.check(len(editors) >= 1, f"Editor widget found (got {len(editors)})")
t.check(len(buttons) >= 10, f"At least 10 buttons found (got {len(buttons)})")

panel_names = [p.get_name() or '' for p in panels]
t.check('Clipboard' in panel_names, "Clipboard frame is present")
t.check('Widget Actions' in panel_names, "Widget Actions frame is present")

expected_buttons = ['Select All', 'Cut', 'Copy', 'Paste',
                    'Disable', 'Enable', 'Clear', 'Delete', 'Refresh', 'Save']
for name in expected_buttons:
    t.check(find_button(buttons, name) is not None,
            f"'{name}' button is present")

editor = editors[0]

# --- Test 2: Initial content loaded from file ---
t.begin("testInitialContent")
text = get_editor_text(editor)
t.check('This text was loaded from an input file' in text,
        "Editor contains text from input file")

# --- Test 3: Select All + Cut ---
t.begin("testSelectAllCut")
do_action(find_button(buttons, 'Select All'), 'click')
time.sleep(0.3)
do_action(find_button(buttons, 'Cut'), 'click')
time.sleep(0.3)
text = get_editor_text(editor)
t.check(text == '', f"Editor is empty after Select All + Cut (got '{text}')")

# --- Test 4: Paste ---
t.begin("testPaste")
do_action(find_button(buttons, 'Paste'), 'click')
time.sleep(0.3)
text = get_editor_text(editor)
t.check('This text was loaded from an input file' in text,
        "Editor has text restored after Paste")

# --- Test 5: Select All + Copy (non-destructive) ---
t.begin("testSelectAllCopy")
do_action(find_button(buttons, 'Select All'), 'click')
time.sleep(0.3)
do_action(find_button(buttons, 'Copy'), 'click')
time.sleep(0.3)
text = get_editor_text(editor)
t.check('This text was loaded from an input file' in text,
        "Editor text preserved after Select All + Copy")

# --- Test 6: Clear ---
t.begin("testClear")
do_action(find_button(buttons, 'Clear'), 'click')
time.sleep(0.3)
text = get_editor_text(editor)
t.check(text == '', f"Editor is empty after Clear (got '{text}')")

# --- Test 7: Refresh ---
t.begin("testRefresh")
do_action(find_button(buttons, 'Refresh'), 'click')
time.sleep(0.3)
text = get_editor_text(editor)
t.check('This text was loaded from an input file' in text,
        "Editor reloaded from file after Refresh")

# --- Test 8: Disable / Enable ---
t.begin("testDisableEnable")
do_action(find_button(buttons, 'Disable'), 'click')
time.sleep(0.3)
t.check(not editor.get_state_set().contains(Atspi.StateType.SENSITIVE),
        "Editor is disabled after Disable")

do_action(find_button(buttons, 'Enable'), 'click')
time.sleep(0.3)
t.check(editor.get_state_set().contains(Atspi.StateType.SENSITIVE),
        "Editor is re-enabled after Enable")

# --- Test 9: OK closes dialog with action output ---
t.begin("testOkOutput")
do_action(find_button(buttons, 'OK'), 'click')
time.sleep(1)

retcode = proc.poll()
if t.check(retcode is not None,
           f"Dialog closed after OK click (exit code {retcode})"
           if retcode is not None
           else "Dialog should have closed after OK click"):
    stdout = proc.stdout.read().decode()
    t.log(f"stdout (first 500 chars): {stdout[:500]}")

    t.check('action:selectall' in stdout,
            "selectall action printed to stdout")
    t.check('action:cut' in stdout,
            "cut action printed to stdout")
    t.check('action:paste' in stdout,
            "paste action printed to stdout")
    t.check('action:clear' in stdout,
            "clear action printed to stdout")
    t.check('action:refresh' in stdout,
            "refresh action printed to stdout")
    t.check('EXIT="OK"' in stdout,
            "EXIT is 'OK' in output")
else:
    proc.kill()

t.summary()

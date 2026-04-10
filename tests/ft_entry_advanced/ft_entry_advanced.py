#!/usr/bin/env python3
"""
Automated test for examples/entry/entry_advanced using AT-SPI2.

Verifies:
1. Widget presence: entries, buttons, frame
2. Default values in entry widgets
3. Editable property (editable="false")
4. Input from shell command
5. Input from file
6. Disable/Enable button actions
7. Clear and Refresh button actions
8. OK button closes dialog and prints selected values
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


def get_entry_text(entry):
    """Get text from an entry widget via AT-SPI."""
    return Atspi.Text.get_text(entry, 0, -1)


def set_entry_text(entry, text):
    """Clear and set text in an editable entry via AT-SPI."""
    iface = entry.get_editable_text_iface()
    if iface is None:
        return False
    old_len = Atspi.Text.get_character_count(entry)
    if old_len > 0:
        Atspi.EditableText.delete_text(entry, 0, old_len)
    Atspi.EditableText.insert_text(entry, 0, text, len(text))
    return True


t = TestRunner()

# Launch the example
t.log("Launching entry_advanced example...")
proc = subprocess.Popen(
    ['./examples/entry/entry_advanced'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(2)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('Entry Advanced')
t.screenshot('Entry Advanced')

if window is None:
    proc.kill()
    t.abort("Could not find Entry Advanced window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")

# Gather widgets
entries = find_widgets(window, Atspi.Role.TEXT)
buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
panels = find_widgets(window, Atspi.Role.PANEL)
t.log(f"Found {len(entries)} entries, {len(buttons)} buttons, {len(panels)} panels")

# --- Test 1: Widget presence ---
t.begin("testWidgetPresence")
t.check('Entry Advanced' in (window.get_name() or ''),
        "Window title is 'Entry Advanced'")
t.check(len(entries) >= 19,
        f"At least 19 text entries found (got {len(entries)})")
t.check(len(buttons) >= 15,
        f"At least 15 buttons found (got {len(buttons)})")

ok_button = None
for b in buttons:
    if 'ok' in (b.get_name() or '').lower():
        ok_button = b
        break
t.check(ok_button is not None, "OK button is present")

panel_names = [p.get_name() or '' for p in panels]
t.check(any('entry widget' in n for n in panel_names),
        "Frame 'entry widget' panel is present")

# --- Test 2: Default values ---
t.begin("testDefaultValues")
expected_defaults = {
    0: 'activates-default',
    1: 'editable',
    2: 'has-frame',
    3: 'max-length',
    8: 'progress-fraction',
    15: 'width-chars',
    17: 'xalign',
}
for idx, expected_text in expected_defaults.items():
    if idx < len(entries):
        actual = get_entry_text(entries[idx])
        t.check(actual == expected_text,
                f"Entry[{idx}] text is '{expected_text}' (got '{actual}')")
    else:
        t.check(False, f"Entry[{idx}] does not exist")

# --- Test 3: Editable property ---
t.begin("testEditableProperty")
if len(entries) >= 2:
    states0 = entries[0].get_state_set()
    t.check(states0.contains(Atspi.StateType.EDITABLE),
            "Entry[0] is editable")

    states1 = entries[1].get_state_set()
    t.check(not states1.contains(Atspi.StateType.EDITABLE),
            "Entry[1] (editable='false') is not editable")

# --- Test 4: Input by command ---
t.begin("testInputByCommand")
if len(entries) >= 19:
    text18 = get_entry_text(entries[18])
    t.check(text18 == 'This came from a shell command, and function signals are blocked',
            f"Entry[18] has text from shell command (got '{text18}')")

# --- Test 5: Input by file ---
t.begin("testInputByFile")
if len(entries) >= 20:
    text19 = get_entry_text(entries[19])
    t.check(text19 == 'This came from an input file',
            f"Entry[19] has text from input file (got '{text19}')")

# --- Test 6: Disable/Enable ---
t.begin("testDisableEnable")
# Find the first Disable and Enable buttons (they act on entry[18])
disable_btn = None
enable_btn = None
for b in buttons:
    name = b.get_name() or ''
    if name == 'Disable' and disable_btn is None:
        disable_btn = b
    elif name == 'Enable' and enable_btn is None:
        enable_btn = b

if disable_btn and enable_btn and len(entries) >= 19:
    do_action(disable_btn, 'click')
    time.sleep(0.5)
    states = entries[18].get_state_set()
    t.check(not states.contains(Atspi.StateType.SENSITIVE),
            "Entry[18] is disabled after Disable click")

    do_action(enable_btn, 'click')
    time.sleep(0.5)
    states = entries[18].get_state_set()
    t.check(states.contains(Atspi.StateType.SENSITIVE),
            "Entry[18] is re-enabled after Enable click")
else:
    t.check(False, "Disable/Enable buttons not found")

# --- Test 7: Clear and Refresh ---
t.begin("testClearRefresh")
clear_btn = None
refresh_btn = None
for b in buttons:
    name = b.get_name() or ''
    if name == 'Clear' and clear_btn is None:
        clear_btn = b
    elif name == 'Refresh' and refresh_btn is None:
        refresh_btn = b

if clear_btn and refresh_btn and len(entries) >= 19:
    do_action(clear_btn, 'click')
    time.sleep(0.5)
    text = get_entry_text(entries[18])
    t.check(text == '',
            f"Entry[18] is empty after Clear (got '{text}')")

    do_action(refresh_btn, 'click')
    time.sleep(0.5)
    text = get_entry_text(entries[18])
    t.check(text == 'This came from a shell command, and function signals are blocked',
            f"Entry[18] restored after Refresh (got '{text}')")
else:
    t.check(False, "Clear/Refresh buttons not found")

# --- Test 8: Edit and output ---
t.begin("testEditAndOutput")
if len(entries) >= 1 and ok_button:
    set_entry_text(entries[0], 'test_value_42')
    time.sleep(0.5)

    actual = get_entry_text(entries[0])
    t.check(actual == 'test_value_42',
            f"Entry[0] text set to 'test_value_42' (got '{actual}')")

    # Click OK, retry once if needed (focus may delay first click)
    do_action(ok_button, 'click')
    time.sleep(2)
    if proc.poll() is None:
        do_action(ok_button, 'click')
        time.sleep(1)

    retcode = proc.poll()
    if t.check(retcode is not None,
               f"Dialog closed after OK click (exit code {retcode})"
               if retcode is not None
               else "Dialog should have closed after OK click"):
        stdout = proc.stdout.read().decode()
        t.log(f"stdout (first 500 chars): {stdout[:500]}")
        t.check('entEntry0="test_value_42"' in stdout,
                "entEntry0 is 'test_value_42' in output")
        t.check('EXIT="OK"' in stdout,
                "EXIT is 'OK' in output")
    else:
        proc.kill()
else:
    t.check(False, "Cannot test edit and output")
    proc.kill()

t.summary()

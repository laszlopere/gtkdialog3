#!/usr/bin/env python3
"""
Automated test for examples/standard/entry using AT-SPI.

Verifies:
1. Window appears with the expected entry widget
2. Entry has the correct default value
3. Modifying the entry value works
4. Clicking OK produces valid JSON output with correct structure
5. JSON contains the widget value under the correct window key
"""

import json
import subprocess
import sys
import time

import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi

sys.path.insert(0, sys.path[0] + '/..')
from testlib import TestRunner, launch, wait_for_window, unique_app_name

TIMEOUT = 10


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
t.log("Launching entry example...")
APP_NAME = unique_app_name()
proc = launch(['./examples/standard/entry'], APP_NAME)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window(APP_NAME, 'System Configuration')
t.screenshot('System Configuration')

if window is None:
    proc.kill()
    t.abort("Could not find System Configuration window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")

# --- Test 1: Entry widget present with default value ---
t.begin("testDefaultValue")
entries = find_widgets(window, Atspi.Role.TEXT)
t.check(len(entries) >= 1, f"At least 1 entry found (got {len(entries)})")
if entries:
    text = Atspi.Text.get_text(entries[0], 0, -1)
    t.check(text == 'localhost',
            f"Entry has default value 'localhost' (got '{text}')")

# --- Test 2: Modify entry and click OK, verify JSON output ---
t.begin("testJsonOutput")

# Set a new value in the entry
if entries:
    ei = entries[0].get_editable_text_iface()
    if ei:
        # Select all and replace
        Atspi.EditableText.delete_text(ei, 0, -1)
        Atspi.EditableText.insert_text(ei, 0, 'my-server', len('my-server'))
        time.sleep(0.3)

# Click OK
buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
ok_button = None
for b in buttons:
    if 'ok' in (b.get_name() or '').lower():
        ok_button = b
        break

if ok_button:
    do_action(ok_button, 'click')
    time.sleep(1)

    retcode = proc.poll()
    if not t.check(retcode is not None,
                   f"Dialog closed after OK click (exit code {retcode})"
                   if retcode is not None
                   else "Dialog should have closed after OK click"):
        proc.kill()
        proc.wait(timeout=3)

    stdout = proc.stdout.read().decode()
    t.log(f"stdout: {repr(stdout)}")

    # Parse JSON
    data = None
    try:
        data = json.loads(stdout)
        t.check(True, "Output is valid JSON")
    except json.JSONDecodeError as e:
        t.check(False, f"Output is valid JSON (parse error: {e})")

    if data is not None:
        # Check top-level structure
        t.check('widget_contents' in data,
                "'widget_contents' key present in JSON")
        t.check('exit' in data,
                "'exit' key present in JSON")

        # Check exit value
        t.check(data.get('exit') == 'OK',
                f"exit is 'OK' (got '{data.get('exit')}')")

        # Check widget_contents has exactly one window
        wc = data.get('widget_contents', {})
        t.check(len(wc) == 1,
                f"Exactly one window in widget_contents (got {len(wc)})")

        # Check the window key name
        t.check('entryDialog' in wc,
                f"Window key is 'entryDialog' (keys: {list(wc.keys())})")

        # Check the entry value under the window key
        window_data = wc.get('entryDialog', {})
        t.check('entHostname' in window_data,
                f"'entHostname' key in window data (keys: {list(window_data.keys())})")
        t.check(window_data.get('entHostname') == 'my-server',
                f"entHostname is 'my-server' (got '{window_data.get('entHostname')}')")
else:
    t.check(False, "OK button not found")
    proc.kill()

t.summary()

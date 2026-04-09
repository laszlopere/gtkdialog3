#!/usr/bin/env python3
"""
Automated test for examples/entry/entry_quote_in_value using AT-SPI2.

Verifies that double quotes in entry values are properly escaped
in the program output so that shell eval works correctly.
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


t = TestRunner()

# Launch the example
t.log("Launching entry_quote_in_value example...")
proc = subprocess.Popen(
    ['./examples/entry/entry_quote_in_value'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('Quote in Value')

if window is None:
    proc.kill()
    t.abort("Could not find Quote in Value window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")

# --- Test 1: Default value with quotes ---
t.begin("testDefaultValue")
entries = find_widgets(window, Atspi.Role.TEXT)
t.check(len(entries) >= 1, f"At least 1 entry found (got {len(entries)})")
if entries:
    text = Atspi.Text.get_text(entries[0], 0, -1)
    t.check(text == 'He said "hello"',
            f"Entry has default value with quotes (got '{text}')")

# --- Test 2: Click OK and check escaped output ---
t.begin("testEscapedOutput")
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
    if t.check(retcode is not None,
               f"Dialog closed after OK click (exit code {retcode})"
               if retcode is not None
               else "Dialog should have closed after OK click"):
        stdout = proc.stdout.read().decode()
        t.log(f"stdout: {repr(stdout)}")

        t.check('ENTRY="He said \\"hello\\""' in stdout,
                "Quotes in value are escaped with backslash")
        t.check('EXIT="OK"' in stdout,
                "EXIT is 'OK' in output")

        # Verify the output is valid for shell eval
        result = subprocess.run(
            ['sh', '-c', stdout + '\necho "$ENTRY"'],
            capture_output=True, text=True)
        t.check(result.returncode == 0,
                f"Shell eval succeeds (exit code {result.returncode})")
        t.check(result.stdout.strip() == 'He said "hello"',
                f"Shell eval produces correct value (got '{result.stdout.strip()}')")
    else:
        proc.kill()
else:
    t.check(False, "OK button not found")
    proc.kill()

t.summary()

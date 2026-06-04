#!/usr/bin/env python3
"""
Automated test for examples/languages/bash_script_event_driven using AT-SPI2.

Verifies:
1. The window appears with the expected title
2. The descriptive label is present and contains expected text
3. The button invokes the exported bash function (stdout check)
4. The Exit button closes the dialog
"""

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
t.log("Launching bash_script_event_driven example...")
APP_NAME = unique_app_name()
proc = launch(['./examples/languages/bash_script_event_driven'], APP_NAME)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window(APP_NAME, 'Bash Event Driven')
t.screenshot('Bash Event Driven')

if window is None:
    proc.kill()
    t.abort("Could not find 'Bash Event Driven' window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")

# --- Test 1: Descriptive label is present ---
t.begin("testDescriptiveLabel")
labels = find_widgets(window, Atspi.Role.LABEL)
found_label = False
for lbl in labels:
    text = lbl.get_name() or ''
    if 'export -f' in text:
        found_label = True
        t.check(True, f"Label contains expected text ({len(text)} chars)")
        break
if not found_label:
    t.check(False, "Could not find descriptive label with expected text")

# --- Test 2: Button calls exported bash function ---
t.begin("testBashFunctionCall")
buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
func_button = None
exit_button = None
for b in buttons:
    name = (b.get_name() or '').lower()
    if 'print_this' in name:
        func_button = b
    elif 'exit' in name:
        exit_button = b

if func_button:
    do_action(func_button, 'click')
    time.sleep(0.5)
    # The function prints to stdout, check it
    import select
    if select.select([proc.stdout], [], [], 1.0)[0]:
        output = proc.stdout.readline().decode().strip()
        t.check(output == 'print: button',
                f"Function output: '{output}'"
                if output == 'print: button'
                else f"Expected 'print: button', got '{output}'")
    else:
        t.check(False, "No output from function call")
else:
    t.check(False, "Could not find function button")

# --- Test 3: Exit button closes dialog ---
t.begin("testExitButton")
if exit_button:
    do_action(exit_button, 'click')
    time.sleep(1)

    retcode = proc.poll()
    if t.check(retcode is not None,
               f"Dialog closed after Exit click (exit code {retcode})"
               if retcode is not None
               else "Dialog should have closed after Exit click"):
        pass
    else:
        proc.kill()
else:
    t.check(False, "Could not find Exit button")
    proc.kill()

t.summary()

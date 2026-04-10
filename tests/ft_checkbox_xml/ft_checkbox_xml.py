#!/usr/bin/env python3
"""
Automated test for examples/standard/checkbox using AT-SPI.

Verifies:
1. Window appears with the expected checkbox widgets
2. Default checkbox states are correct
3. Toggling checkboxes changes their state
4. Clicking OK produces valid XML output with correct structure
5. XML contains the checkbox values under the correct window key
"""

import subprocess
import sys
import time
import xml.etree.ElementTree as ET

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


def is_checked(widget):
    """Check if a checkbox is checked."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.CHECKED)


t = TestRunner()

# Launch the example
t.log("Launching checkbox example...")
proc = subprocess.Popen(
    ['./examples/standard/checkbox'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('Package Selection')

if window is None:
    proc.kill()
    t.abort("Could not find Package Selection window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")

# Find checkboxes
checkboxes = find_widgets(window, Atspi.Role.CHECK_BOX)
t.log(f"Found {len(checkboxes)} checkboxes")

# --- Test 1: Initial checkbox states ---
t.begin("testInitialState")
t.check(len(checkboxes) == 6, f"Found 6 checkboxes (got {len(checkboxes)})")
if len(checkboxes) >= 6:
    t.check(is_checked(checkboxes[0]),
            "chkBase is checked (default=true)")
    t.check(not is_checked(checkboxes[1]),
            "chkDevel is unchecked")

# --- Test 2: Toggle chkDevel on ---
t.begin("testToggleCheckbox")
if len(checkboxes) >= 2:
    do_action(checkboxes[1], 'click')
    time.sleep(0.3)
    t.check(is_checked(checkboxes[1]), "chkDevel is now checked after toggle")

# --- Test 3: Click OK and verify XML output ---
t.begin("testXmlOutput")
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

    # Parse XML
    root = None
    try:
        root = ET.fromstring(stdout)
        t.check(True, "Output is valid XML")
    except ET.ParseError as e:
        t.check(False, f"Output is valid XML (parse error: {e})")

    if root is not None:
        # Check root element
        t.check(root.tag == 'gtkdialog',
                f"Root element is <gtkdialog> (got <{root.tag}>)")

        # Check widget_contents
        wc = root.find('widget_contents')
        t.check(wc is not None, "<widget_contents> element present")

        # Check exit
        exit_el = root.find('exit')
        t.check(exit_el is not None and exit_el.text == 'OK',
                f"<exit> is 'OK' (got '{exit_el.text if exit_el is not None else None}')")

        if wc is not None:
            # Check window element
            win_el = wc.find('window[@name="checkboxDialog"]')
            t.check(win_el is not None,
                    "Window 'checkboxDialog' found in XML")

            if win_el is not None:
                # Collect variables into a dict
                xml_vars = {v.get('name'): v.text
                            for v in win_el.findall('variable')}

                t.check('chkBase' in xml_vars,
                        f"'chkBase' in XML (keys: {list(xml_vars.keys())})")
                t.check(xml_vars.get('chkBase') == 'true',
                        f"chkBase is 'true' (got '{xml_vars.get('chkBase')}')")

                t.check('chkDevel' in xml_vars,
                        f"'chkDevel' in XML (keys: {list(xml_vars.keys())})")
                t.check(xml_vars.get('chkDevel') == 'true',
                        f"chkDevel is 'true' after toggle (got '{xml_vars.get('chkDevel')}')")

                t.check(xml_vars.get('chkOffice') == 'false',
                        f"chkOffice is 'false' (got '{xml_vars.get('chkOffice')}')")
else:
    t.check(False, "OK button not found")
    proc.kill()

t.summary()

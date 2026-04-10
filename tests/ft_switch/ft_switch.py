#!/usr/bin/env python3
"""
Automated test for examples/switch/switch using AT-SPI2.

Verifies:
1. Window appears with expected title
2. Two switch (toggle button) widgets are present
3. Default states are correct (NOTIFICATIONS=true, DARKMODE=false)
4. Toggling a switch changes its state
5. OK button closes dialog and prints correct values
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


def is_checked(widget):
    """Check if a toggle widget is in the checked/active state."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.CHECKED)


t = TestRunner()

# Launch the example
t.log("Launching switch example...")
proc = subprocess.Popen(
    ['./examples/switch/switch'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('Switch Demo')
t.screenshot('Switch Demo')

if window is None:
    proc.kill()
    t.abort("Could not find Switch Demo window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")

# Find widgets
toggles = find_widgets(window, Atspi.Role.TOGGLE_BUTTON)
buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
labels = find_widgets(window, Atspi.Role.LABEL)

# --- Test 1: Widget presence ---
t.begin("testWidgetPresence")
t.check('Switch Demo' in (window.get_name() or ''),
        "Window title is 'Switch Demo'")
t.check(len(toggles) == 2,
        f"Found 2 switch widgets (got {len(toggles)})")
t.check(any('ok' in (b.get_name() or '').lower() for b in buttons),
        "OK button is present")
t.check(any('notifications' in (l.get_name() or '').lower() for l in labels),
        "Notifications label is present")
t.check(any('dark mode' in (l.get_name() or '').lower() for l in labels),
        "Dark mode label is present")

# --- Test 2: Default states ---
t.begin("testDefaultStates")
if len(toggles) >= 2:
    t.check(is_checked(toggles[0]),
            "First switch (NOTIFICATIONS) is ON by default")
    t.check(not is_checked(toggles[1]),
            "Second switch (DARKMODE) is OFF by default")

# --- Test 3: Toggle switches ---
t.begin("testToggle")
if len(toggles) >= 2:
    # Toggle NOTIFICATIONS off
    do_action(toggles[0], 'toggle')
    time.sleep(0.5)
    t.check(not is_checked(toggles[0]),
            "First switch is OFF after toggle")

    # Toggle DARKMODE on
    do_action(toggles[1], 'toggle')
    time.sleep(0.5)
    t.check(is_checked(toggles[1]),
            "Second switch is ON after toggle")

# --- Test 4: Output values ---
t.begin("testOutput")
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
        t.check('NOTIFICATIONS="false"' in stdout,
                "NOTIFICATIONS is 'false' in output (was toggled off)")
        t.check('DARKMODE="true"' in stdout,
                "DARKMODE is 'true' in output (was toggled on)")
        t.check('EXIT="OK"' in stdout,
                "EXIT is 'OK' in output")
    else:
        proc.kill()
else:
    t.check(False, "OK button not found")
    proc.kill()

t.summary()

#!/usr/bin/env python3
"""
Automated test for examples/checkbox/checkbox using AT-SPI2.

Launches the checkbox example dialog and verifies:
1. The window appears with the expected widgets
2. The first checkbox toggles and enables/disables the entry
3. The second checkbox controls the OK button sensitivity
4. Clicking OK closes the dialog
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


def wait_for_window(name_substring, timeout=TIMEOUT):
    """Wait for a window matching the name to appear in AT-SPI tree."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        desktop = Atspi.get_desktop(0)
        for i in range(desktop.get_child_count()):
            app = desktop.get_child_at_index(i)
            if app is None:
                continue
            for j in range(app.get_child_count()):
                win = app.get_child_at_index(j)
                if win and name_substring.lower() in (win.get_name() or '').lower():
                    return app, win
        time.sleep(0.3)
    return None, None


def find_widgets(node, role=None, depth=0):
    """Recursively find all widgets, optionally filtered by role."""
    results = []
    if node is None:
        return results
    try:
        node_role = node.get_role()
        node_name = node.get_name() or ''
    except Exception:
        return results

    if role is None or node_role == role:
        results.append(node)

    for i in range(node.get_child_count()):
        child = node.get_child_at_index(i)
        results.extend(find_widgets(child, role, depth + 1))
    return results


def dump_tree(node, indent=0):
    """Debug helper: print the AT-SPI widget tree."""
    if node is None:
        return
    try:
        role = node.get_role_name()
        name = node.get_name() or ''
        states = node.get_state_set()
        enabled = states.contains(Atspi.StateType.ENABLED)
        checked = states.contains(Atspi.StateType.CHECKED)
        print(f"{'  ' * indent}{role}: '{name}' enabled={enabled} checked={checked}")
    except Exception as e:
        print(f"{'  ' * indent}(error: {e})")
        return
    for i in range(node.get_child_count()):
        dump_tree(node.get_child_at_index(i), indent + 1)


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


def is_enabled(widget):
    """Check if a widget is sensitive/enabled."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.SENSITIVE)


def is_checked(widget):
    """Check if a checkbox is checked."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.CHECKED)


t = TestRunner()

# Launch the checkbox example
t.log("Launching checkbox example...")
proc = subprocess.Popen(
    ['./examples/checkbox/checkbox'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

# Give it time to start up
time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('gtkdialog3')

if window is None:
    proc.kill()
    t.abort("Could not find gtkdialog3 window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")
if t.verbose:
    print()
    print("Widget tree:")
    dump_tree(window)
    print()

# Find checkboxes
checkboxes = find_widgets(window, Atspi.Role.CHECK_BOX)
t.log(f"Found {len(checkboxes)} checkboxes")

# Find buttons
buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
t.log(f"Found {len(buttons)} buttons")

# Find text entry
entries = find_widgets(window, Atspi.Role.TEXT)
if not entries:
    entries = find_widgets(window, Atspi.Role.ENTRY)
t.log(f"Found {len(entries)} text entries")

# --- Test 1: Initial state ---
t.begin("testInitialState")
if len(checkboxes) >= 2:
    cb1 = checkboxes[0]
    cb2 = checkboxes[1]

    t.check(not is_checked(cb1),
            "First checkbox is unchecked initially")
    t.check(is_checked(cb2),
            "Second checkbox is checked initially (default=true)")
else:
    t.check(False, f"Expected 2 checkboxes, found {len(checkboxes)}")

if entries:
    entry = entries[0]
    t.check(not is_enabled(entry),
            "Entry is disabled initially (sensitive=false)")

# Find OK button
ok_button = None
for b in buttons:
    if 'ok' in (b.get_name() or '').lower() or 'gtk-ok' in (b.get_name() or '').lower():
        ok_button = b
        break
if ok_button is None and buttons:
    ok_button = buttons[0]

t.check(ok_button and is_enabled(ok_button),
        "OK button is enabled initially (second checkbox is true)")

# --- Test 2: Toggle first checkbox -> entry should become enabled ---
t.begin("testToggleFirst")
if len(checkboxes) >= 1:
    do_action(cb1, 'click')
    time.sleep(0.5)

    t.check(is_checked(cb1),
            "First checkbox is now checked")
    t.check(entries and is_enabled(entries[0]),
            "Entry is now enabled")

# --- Test 3: Toggle second checkbox -> OK button should become disabled ---
t.begin("testToggleSecond")
if len(checkboxes) >= 2:
    do_action(cb2, 'click')
    time.sleep(0.5)

    t.check(not is_checked(cb2),
            "Second checkbox is now unchecked")
    t.check(ok_button and not is_enabled(ok_button),
            "OK button is now disabled")

# --- Test 4: Re-enable OK and click it to close ---
t.begin("testCloseDialog")
if len(checkboxes) >= 2:
    do_action(cb2, 'click')  # re-check to enable OK
    time.sleep(0.5)

    if ok_button:
        do_action(ok_button, 'click')
        time.sleep(1)

        retcode = proc.poll()
        if t.check(retcode is not None,
                   f"Dialog closed after OK click (exit code {retcode})"
                   if retcode is not None
                   else "Dialog should have closed after OK click"):
            pass
        else:
            proc.kill()

t.summary()

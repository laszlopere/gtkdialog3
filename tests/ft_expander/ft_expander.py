#!/usr/bin/env python3
"""
Automated test for examples/expander/expander using AT-SPI2.

Launches the expander example dialog and verifies:
1. The window appears with the expected widgets
2. The expander starts expanded with correct child widgets
3. Checkboxes have the correct initial active states
4. Collapsing and expanding the expander works
5. Clicking Quit closes the dialog
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
            app_name = (app.get_name() or '').lower()
            if 'gtkdialog' not in app_name:
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
        expanded = states.contains(Atspi.StateType.EXPANDED)
        checked = states.contains(Atspi.StateType.CHECKED)
        print(f"{'  ' * indent}{role}: '{name}' expanded={expanded} checked={checked}")
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


def is_checked(widget):
    """Check if a checkbox is checked."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.CHECKED)


def is_expanded(widget):
    """Check if a widget is in the expanded state."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.EXPANDED)


t = TestRunner()

# Launch the expander example
t.log("Launching expander example...")
proc = subprocess.Popen(
    ['./examples/expander/expander'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('Expander')

if window is None:
    proc.kill()
    t.abort("Could not find Expander window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")
if t.verbose:
    print()
    print("Widget tree:")
    dump_tree(window)
    print()

# --- Test 1: Initial state ---
t.begin("testInitialState")

# Find the expander widget
# AT-SPI may expose it as a panel or toggle button; search by role name
all_widgets = find_widgets(window)
expander = None
for w in all_widgets:
    try:
        if w.get_role_name() == 'toggle button' and 'xpander' in (w.get_name() or ''):
            expander = w
            break
    except Exception:
        continue

# If not found as toggle button, look for a panel with the expander label
if expander is None:
    for w in all_widgets:
        try:
            role_name = w.get_role_name()
            name = w.get_name() or ''
            if 'xpander' in name:
                expander = w
                break
        except Exception:
            continue

t.check(expander is not None, "Expander widget found")

if expander is not None:
    t.check(is_expanded(expander), "Expander is expanded initially (expanded='true')")

# Find checkboxes - the example has 4 with active: false, true, false, true
checkboxes = find_widgets(window, Atspi.Role.CHECK_BOX)
t.check(len(checkboxes) >= 4, f"Found at least 4 checkboxes (got {len(checkboxes)})")

if len(checkboxes) >= 4:
    expected = [False, True, False, True]
    for i, exp in enumerate(expected):
        actual = is_checked(checkboxes[i])
        t.check(actual == exp,
                f"Checkbox {i+1} is {'checked' if exp else 'unchecked'} "
                f"(expected={exp}, actual={actual})")

# Find entries
entries = find_widgets(window, Atspi.Role.TEXT)
if not entries:
    entries = find_widgets(window, Atspi.Role.ENTRY)
t.check(len(entries) >= 4, f"Found at least 4 text entries (got {len(entries)})")

# Find buttons
buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
t.check(len(buttons) >= 9, f"Found at least 9 buttons (got {len(buttons)})")

t.screenshot("Expander")

# --- Test 2: Toggle checkbox ---
t.begin("testToggleCheckbox")
if len(checkboxes) >= 1:
    cb = checkboxes[0]
    t.check(not is_checked(cb), "First checkbox starts unchecked")

    do_action(cb, 'click')
    time.sleep(0.5)

    t.check(is_checked(cb), "First checkbox is checked after click")

    # Toggle back
    do_action(cb, 'click')
    time.sleep(0.5)

    t.check(not is_checked(cb), "First checkbox unchecked after second click")

# --- Test 3: Collapse and expand the expander ---
t.begin("testExpanderToggle")
if expander is not None:
    t.check(is_expanded(expander), "Expander starts expanded")

    do_action(expander)
    time.sleep(0.5)

    t.check(not is_expanded(expander), "Expander collapsed after action")

    do_action(expander)
    time.sleep(0.5)

    t.check(is_expanded(expander), "Expander expanded again after second action")

# --- Test 4: Close via Quit button ---
t.begin("testCloseDialog")
quit_button = None
for b in buttons:
    name = (b.get_name() or '').lower()
    if 'quit' in name or 'gtk-quit' in name:
        quit_button = b
        break

if t.check(quit_button is not None, "Quit button found"):
    do_action(quit_button, 'click')
    time.sleep(1)

    retcode = proc.poll()
    if not t.check(retcode is not None,
                   f"Dialog closed after Quit click (exit code {retcode})"
                   if retcode is not None
                   else "Dialog should have closed after Quit click"):
        proc.kill()
else:
    proc.kill()

t.summary()

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


def test_pass(msg):
    print(f"  PASS: {msg}")


def test_fail(msg):
    print(f"  FAIL: {msg}")
    global failures
    failures += 1


failures = 0

# Launch the checkbox example
print("Launching checkbox example...")
proc = subprocess.Popen(
    ['./examples/checkbox/checkbox'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

# Give it time to start up
time.sleep(1)

print("Looking for window via AT-SPI...")
app, window = wait_for_window('gtkdialog3')

if window is None:
    print("FAIL: Could not find gtkdialog3 window via AT-SPI")
    proc.kill()
    sys.exit(1)

print(f"Found window: '{window.get_name()}'")
print()
print("Widget tree:")
dump_tree(window)
print()

# Find checkboxes
checkboxes = find_widgets(window, Atspi.Role.CHECK_BOX)
print(f"Found {len(checkboxes)} checkboxes")

# Find buttons
buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
print(f"Found {len(buttons)} buttons")

# Find text entry
entries = find_widgets(window, Atspi.Role.TEXT)
if not entries:
    entries = find_widgets(window, Atspi.Role.ENTRY)
print(f"Found {len(entries)} text entries")
print()

# --- Test 1: Initial state ---
print("Test 1: Initial state")
if len(checkboxes) >= 2:
    cb1 = checkboxes[0]
    cb2 = checkboxes[1]

    if not is_checked(cb1):
        test_pass("First checkbox is unchecked initially")
    else:
        test_fail("First checkbox should be unchecked initially")

    if is_checked(cb2):
        test_pass("Second checkbox is checked initially (default=true)")
    else:
        test_fail("Second checkbox should be checked initially")
else:
    test_fail(f"Expected 2 checkboxes, found {len(checkboxes)}")

if entries:
    entry = entries[0]
    if not is_enabled(entry):
        test_pass("Entry is disabled initially (sensitive=false)")
    else:
        test_fail("Entry should be disabled initially")

# Find OK button
ok_button = None
for b in buttons:
    if 'ok' in (b.get_name() or '').lower() or 'gtk-ok' in (b.get_name() or '').lower():
        ok_button = b
        break
# If we can't find by name, take the first button
if ok_button is None and buttons:
    ok_button = buttons[0]

if ok_button and is_enabled(ok_button):
    test_pass("OK button is enabled initially (second checkbox is true)")
else:
    test_fail("OK button should be enabled initially")

# --- Test 2: Toggle first checkbox -> entry should become enabled ---
print("\nTest 2: Toggle first checkbox")
if len(checkboxes) >= 1:
    do_action(cb1, 'click')
    time.sleep(0.5)

    if is_checked(cb1):
        test_pass("First checkbox is now checked")
    else:
        test_fail("First checkbox should be checked after click")

    if entries and is_enabled(entries[0]):
        test_pass("Entry is now enabled")
    else:
        test_fail("Entry should be enabled when first checkbox is checked")

# --- Test 3: Toggle second checkbox -> OK button should become disabled ---
print("\nTest 3: Toggle second checkbox (uncheck)")
if len(checkboxes) >= 2:
    do_action(cb2, 'click')
    time.sleep(0.5)

    if not is_checked(cb2):
        test_pass("Second checkbox is now unchecked")
    else:
        test_fail("Second checkbox should be unchecked after click")

    if ok_button and not is_enabled(ok_button):
        test_pass("OK button is now disabled")
    else:
        test_fail("OK button should be disabled when second checkbox is unchecked")

# --- Test 4: Re-enable OK and click it to close ---
print("\nTest 4: Re-enable OK button and close dialog")
if len(checkboxes) >= 2:
    do_action(cb2, 'click')  # re-check to enable OK
    time.sleep(0.5)

    if ok_button:
        do_action(ok_button, 'click')
        time.sleep(1)

        retcode = proc.poll()
        if retcode is not None:
            test_pass(f"Dialog closed after OK click (exit code {retcode})")
        else:
            test_fail("Dialog should have closed after OK click")
            proc.kill()

# Print summary
print(f"\n{'=' * 40}")
if failures == 0:
    print("All tests PASSED")
    sys.exit(0)
else:
    print(f"{failures} test(s) FAILED")
    sys.exit(1)

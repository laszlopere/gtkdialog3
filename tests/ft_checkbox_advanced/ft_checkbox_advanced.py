#!/usr/bin/env python3
"""
Automated test for examples/checkbox/checkbox_advanced using AT-SPI2.

Launches the checkbox_advanced example dialog and verifies:
1. Initial states of all 6 checkboxes
2. Toggling chk0 enables/disables the File menu
3. Disable/Enable buttons control chk0
4. chk2 (active=false) and chk3 (active=true) initial states
5. chk5 starts in indeterminate state
6. Closing via File > Quit
"""

import subprocess
import sys
import time
import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi

TIMEOUT = 10  # seconds


def wait_for_window(name, pid=None, timeout=TIMEOUT):
    """Wait for a window matching the name to appear in AT-SPI tree.
    If pid is given, also match the application's process ID."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        desktop = Atspi.get_desktop(0)
        for i in range(desktop.get_child_count()):
            app = desktop.get_child_at_index(i)
            if app is None:
                continue
            if pid is not None:
                try:
                    if app.get_process_id() != pid:
                        continue
                except Exception:
                    continue
            for j in range(app.get_child_count()):
                win = app.get_child_at_index(j)
                if win and (win.get_name() or '') == name:
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
        child = node.get_child_at_index(i)
        results.extend(find_widgets(child, role))
    return results


def find_widget_by_name(node, role, name):
    """Find a widget by role and name."""
    for w in find_widgets(node, role):
        if (w.get_name() or '') == name:
            return w
    return None


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


def is_sensitive(widget):
    """Check if a widget is sensitive/enabled."""
    return widget.get_state_set().contains(Atspi.StateType.SENSITIVE)


def is_checked(widget):
    """Check if a checkbox is checked."""
    return widget.get_state_set().contains(Atspi.StateType.CHECKED)


def is_indeterminate(widget):
    """Check if a checkbox is in indeterminate state."""
    return widget.get_state_set().contains(Atspi.StateType.INDETERMINATE)


def test_pass(msg):
    print(f"  PASS: {msg}")


def test_fail(msg):
    print(f"  FAIL: {msg}")
    global failures
    failures += 1


failures = 0

# Launch the example
print("Launching checkbox_advanced example...")
proc = subprocess.Popen(
    ['./examples/checkbox/checkbox_advanced'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

print("Looking for window via AT-SPI...")
app, window = wait_for_window('CheckBox Advanced')

if window is None:
    print("FAIL: Could not find 'CheckBox Advanced' window via AT-SPI")
    proc.kill()
    sys.exit(1)

print(f"Found window: '{window.get_name()}'")

# Gather widgets
checkboxes = find_widgets(window, Atspi.Role.CHECK_BOX)
buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
menus = find_widgets(window, Atspi.Role.MENU)
menu_items = find_widgets(window, Atspi.Role.MENU_ITEM)

print(f"Found {len(checkboxes)} checkboxes, {len(buttons)} buttons, "
      f"{len(menus)} menus, {len(menu_items)} menu items\n")

if len(checkboxes) < 6:
    print(f"FAIL: Expected 6 checkboxes, found {len(checkboxes)}")
    proc.kill()
    sys.exit(1)

chk0 = checkboxes[0]  # Enable/disable the File menu
chk1 = checkboxes[1]  # Enable/disable (block-function-signals)
chk2 = checkboxes[2]  # Initially active=false
chk3 = checkboxes[3]  # Initially active=true
chk4 = checkboxes[4]  # draw-indicator=false
chk5 = checkboxes[5]  # inconsistent=true

# Find File menu
file_menu = find_widget_by_name(window, Atspi.Role.MENU, 'File')

# Find buttons by name in order (first 4 belong to chk0, next 4 to chk1)
btn_disable_0 = buttons[0]
btn_enable_0 = buttons[1]
btn_clear_0 = buttons[2]
btn_refresh_0 = buttons[3]

# --- Test 1: Initial states ---
print("Test 1: Initial checkbox states")

if is_checked(chk0):
    test_pass("chk0 is checked (input echoes true)")
else:
    test_fail("chk0 should be checked initially")

if is_checked(chk1):
    test_pass("chk1 is checked (input echoes true)")
else:
    test_fail("chk1 should be checked initially")

if not is_checked(chk2):
    test_pass("chk2 is unchecked (active=false)")
else:
    test_fail("chk2 should be unchecked (active=false)")

if is_checked(chk3):
    test_pass("chk3 is checked (active=true)")
else:
    test_fail("chk3 should be checked (active=true)")

if not is_checked(chk4):
    test_pass("chk4 is unchecked (draw-indicator=false)")
else:
    test_fail("chk4 should be unchecked initially")

if is_indeterminate(chk5):
    test_pass("chk5 is indeterminate (inconsistent=true)")
else:
    test_fail("chk5 should be in indeterminate state")

# --- Test 2: File menu is sensitive initially ---
print("\nTest 2: File menu initial state")
if file_menu and is_sensitive(file_menu):
    test_pass("File menu is sensitive (chk0 is checked)")
else:
    test_fail("File menu should be sensitive initially")

# --- Test 3: Uncheck chk0 -> File menu should become insensitive ---
print("\nTest 3: Uncheck chk0 -> File menu disabled")
do_action(chk0, 'click')
time.sleep(0.5)

if not is_checked(chk0):
    test_pass("chk0 is now unchecked")
else:
    test_fail("chk0 should be unchecked after click")

if file_menu and not is_sensitive(file_menu):
    test_pass("File menu is now insensitive")
else:
    test_fail("File menu should be insensitive when chk0 is unchecked")

# --- Test 4: Re-check chk0 -> File menu sensitive again ---
print("\nTest 4: Re-check chk0 -> File menu enabled")
do_action(chk0, 'click')
time.sleep(0.5)

if is_checked(chk0):
    test_pass("chk0 is checked again")
else:
    test_fail("chk0 should be checked after second click")

if file_menu and is_sensitive(file_menu):
    test_pass("File menu is sensitive again")
else:
    test_fail("File menu should be sensitive when chk0 is checked")

# --- Test 5: Disable button makes chk0 insensitive ---
print("\nTest 5: Disable button makes chk0 insensitive")
do_action(btn_disable_0, 'click')
time.sleep(0.5)

if not is_sensitive(chk0):
    test_pass("chk0 is insensitive after Disable button")
else:
    test_fail("chk0 should be insensitive after Disable button click")

# --- Test 6: Enable button makes chk0 sensitive again ---
print("\nTest 6: Enable button makes chk0 sensitive")
do_action(btn_enable_0, 'click')
time.sleep(0.5)

if is_sensitive(chk0):
    test_pass("chk0 is sensitive after Enable button")
else:
    test_fail("chk0 should be sensitive after Enable button click")

# --- Test 7: Toggle chk2 and chk3 ---
print("\nTest 7: Toggle chk2 and chk3")
do_action(chk2, 'click')
time.sleep(0.3)

if is_checked(chk2):
    test_pass("chk2 is now checked after click")
else:
    test_fail("chk2 should be checked after click")

do_action(chk3, 'click')
time.sleep(0.3)

if not is_checked(chk3):
    test_pass("chk3 is now unchecked after click")
else:
    test_fail("chk3 should be unchecked after click")

# --- Test 8: Close via File > Quit ---
print("\nTest 8: Close via File > Quit")
if file_menu:
    # Open the File menu first
    do_action(file_menu, 'click')
    time.sleep(0.5)
    quit_item = find_widget_by_name(window, Atspi.Role.MENU_ITEM, 'Quit')
    if quit_item:
        do_action(quit_item, 'click')
        time.sleep(1)

        retcode = proc.poll()
        if retcode is not None:
            test_pass(f"Dialog closed via Quit (exit code {retcode})")
        else:
            test_fail("Dialog should have closed after Quit")
            proc.kill()
    else:
        test_fail("Could not find Quit menu item")
        proc.kill()
else:
    test_fail("Could not find File menu")
    proc.kill()

# Print summary
print(f"\n{'=' * 40}")
if failures == 0:
    print("All tests PASSED")
    sys.exit(0)
else:
    print(f"{failures} test(s) FAILED")
    sys.exit(1)

#!/usr/bin/env python3
"""
Automated test for examples/list/list_actions using AT-SPI2.

Verifies:
1. Window appears with a list containing 3 items
2. First item is selected by default
3. Disable button disables the list
4. Enable button re-enables the list
5. Removeselected removes the selected item
6. Clear button clears all items
7. Refresh reloads items from file
8. Cancel closes the dialog
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


def find_button(window, label_text):
    """Find a push button by its label text."""
    for btn in find_widgets(window, Atspi.Role.PUSH_BUTTON):
        name = (btn.get_name() or '').lower()
        if label_text.lower() == name:
            return btn
    return None


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


def is_enabled(widget):
    """Check if a widget is sensitive/enabled."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.SENSITIVE)


def is_selected(widget):
    """Check if a widget is selected."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.SELECTED)


def get_table_cells(window):
    """Get all table cell widgets (list items)."""
    return find_widgets(window, Atspi.Role.TABLE_CELL)


def dump_tree(node, indent=0):
    """Debug helper: print the AT-SPI widget tree."""
    if node is None:
        return
    try:
        role = node.get_role_name()
        name = node.get_name() or ''
        states = node.get_state_set()
        enabled = states.contains(Atspi.StateType.ENABLED)
        print(f"{'  ' * indent}{role}: '{name}' enabled={enabled}")
    except Exception as e:
        print(f"{'  ' * indent}(error: {e})")
        return
    for i in range(node.get_child_count()):
        dump_tree(node.get_child_at_index(i), indent + 1)


def test_pass(msg):
    print(f"  PASS: {msg}")


def test_fail(msg):
    print(f"  FAIL: {msg}")
    global failures
    failures += 1


failures = 0

# Kill any leftover gtkdialog3 processes
subprocess.run(['pkill', '-x', 'gtkdialog3'], capture_output=True)
time.sleep(0.5)

# Launch the example
print("Launching list_actions example...")
proc = subprocess.Popen(
    ['./examples/list/list_actions'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

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

# --- Test 1: Initial list contents ---
print("Test 1: Initial list contents")
cells = get_table_cells(window)
cell_names = [c.get_name() or '' for c in cells]
expected = ['First item', 'Second item', 'Third item']
if cell_names == expected:
    test_pass(f"List has 3 items: {cell_names}")
else:
    test_fail(f"Expected {expected}, got {cell_names}")

# --- Test 2: First item is selected by default ---
print("\nTest 2: First item selected by default")
if cells and is_selected(cells[0]):
    test_pass("First item is selected")
else:
    test_fail("First item should be selected by default")

# --- Test 3: Disable button disables the list ---
print("\nTest 3: Disable button disables the list")
disable_btn = find_button(window, 'Disable')
if disable_btn:
    do_action(disable_btn, 'click')
    time.sleep(0.5)
    tables = find_widgets(window, Atspi.Role.TABLE)
    if tables and not is_enabled(tables[0]):
        test_pass("List is disabled")
    else:
        test_fail("List should be disabled after clicking Disable")
else:
    test_fail("Disable button not found")

# --- Test 4: Enable button re-enables the list ---
print("\nTest 4: Enable button re-enables the list")
enable_btn = find_button(window, 'Enable')
if enable_btn:
    do_action(enable_btn, 'click')
    time.sleep(0.5)
    tables = find_widgets(window, Atspi.Role.TABLE)
    if tables and is_enabled(tables[0]):
        test_pass("List is enabled again")
    else:
        test_fail("List should be enabled after clicking Enable")
else:
    test_fail("Enable button not found")

# --- Test 5: Removeselected removes the selected item ---
print("\nTest 5: Removeselected removes selected item")
remove_btn = find_button(window, 'Removeselected')
if remove_btn:
    do_action(remove_btn, 'click')
    time.sleep(0.5)
    cells = get_table_cells(window)
    cell_names = [c.get_name() or '' for c in cells]
    if 'First item' not in cell_names and len(cell_names) == 2:
        test_pass(f"Selected item removed, remaining: {cell_names}")
    else:
        test_fail(f"Expected 2 items without 'First item', got {cell_names}")
else:
    test_fail("Removeselected button not found")

# --- Test 6: Clear button clears all items ---
print("\nTest 6: Clear button clears all items")
clear_btn = find_button(window, 'Clear')
if clear_btn:
    do_action(clear_btn, 'click')
    time.sleep(0.5)
    cells = get_table_cells(window)
    if len(cells) == 0:
        test_pass("List is empty after Clear")
    else:
        cell_names = [c.get_name() or '' for c in cells]
        test_fail(f"List should be empty after Clear, got {cell_names}")
else:
    test_fail("Clear button not found")

# --- Test 7: Refresh reloads items from file ---
print("\nTest 7: Refresh reloads items from file")
refresh_btn = find_button(window, 'Refresh')
if refresh_btn:
    do_action(refresh_btn, 'click')
    time.sleep(0.5)
    cells = get_table_cells(window)
    cell_names = [c.get_name() or '' for c in cells]
    if cell_names == expected:
        test_pass(f"Items reloaded: {cell_names}")
    else:
        test_fail(f"Expected {expected} after Refresh, got {cell_names}")
else:
    test_fail("Refresh button not found")

# --- Test 8: Cancel closes the dialog ---
print("\nTest 8: Cancel closes the dialog")
cancel_btn = find_button(window, 'Cancel')
if cancel_btn:
    do_action(cancel_btn, 'click')
    time.sleep(1)
    retcode = proc.poll()
    if retcode is not None:
        test_pass(f"Dialog closed after Cancel (exit code {retcode})")
    else:
        test_fail("Dialog should have closed after Cancel")
        proc.kill()
        proc.wait()
else:
    test_fail("Cancel button not found")
    proc.kill()
    proc.wait()

# Print summary
print(f"\n{'=' * 40}")
if failures == 0:
    print("All tests PASSED")
    sys.exit(0)
else:
    print(f"{failures} test(s) FAILED")
    sys.exit(1)

#!/usr/bin/env python3
"""
Automated test for examples/table/table using AT-SPI2.

Verifies:
1. Window appears with one table widget (4 columns, ~1003 rows)
2. Row 1 is selected by default (selected-row="1")
3. Disable button disables the table
4. Enable button re-enables the table
5. Hide button hides the table
6. Show button makes the table visible again
7. Removeselected removes the selected row
8. Clear button removes all rows
9. Refresh reloads rows from the input sources
10. Quit button closes the dialog
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


def wait_for_window(name_substring, timeout=TIMEOUT, app_name='gtkdialog3'):
    """Wait for a window matching the name to appear in AT-SPI tree."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        desktop = Atspi.get_desktop(0)
        for i in range(desktop.get_child_count()):
            app = desktop.get_child_at_index(i)
            if app is None:
                continue
            if app_name and app_name.lower() not in (app.get_name() or '').lower():
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


def is_visible(widget):
    """Check if a widget is visible."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.VISIBLE)


def is_showing(widget):
    """Check if a widget is showing (mapped on screen)."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.SHOWING)


def get_table_row_count(table):
    """Get the number of rows in a table widget via its table interface."""
    ti = table.get_table_iface()
    if ti is None:
        return -1
    return ti.get_n_rows()


def get_table_col_count(table):
    """Get the number of columns in a table widget via its table interface."""
    ti = table.get_table_iface()
    if ti is None:
        return -1
    return ti.get_n_columns()


def is_row_selected(table, row):
    """Check if a specific row is selected in the table."""
    ti = table.get_table_iface()
    if ti is None:
        return False
    return ti.is_row_selected(row)


def dump_tree(node, indent=0):
    """Debug helper: print the AT-SPI widget tree."""
    if node is None:
        return
    try:
        role = node.get_role_name()
        name = node.get_name() or ''
        states = node.get_state_set()
        enabled = states.contains(Atspi.StateType.ENABLED)
        visible = states.contains(Atspi.StateType.VISIBLE)
        print(f"{'  ' * indent}{role}: '{name}' enabled={enabled} visible={visible}")
    except Exception as e:
        print(f"{'  ' * indent}(error: {e})")
        return
    for i in range(node.get_child_count()):
        dump_tree(node.get_child_at_index(i), indent + 1)


t = TestRunner()

# Kill any leftover gtkdialog3 processes
subprocess.run(['pkill', '-x', 'gtkdialog3'], capture_output=True)
time.sleep(0.5)

# Launch the example
t.log("Launching table example...")
proc = subprocess.Popen(
    ['./examples/table/table'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(2)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('table')
t.screenshot('table')

if window is None:
    # Try generic name as fallback
    app, window = wait_for_window('gtkdialog3')

if window is None:
    proc.kill()
    t.abort("Could not find Table window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")
if t.verbose:
    print()
    print("Widget tree:")
    dump_tree(window)
    print()

# Find the table widget — try TREE_TABLE first, then TABLE
tables = find_widgets(window, Atspi.Role.TREE_TABLE)
if not tables:
    tables = find_widgets(window, Atspi.Role.TABLE)

# --- Test 1: Table present with expected structure ---
t.begin("testTablePresent")
t.check(len(tables) >= 1,
        f"Found {len(tables)} table widget(s)"
        if len(tables) >= 1
        else "No table widget found")

if not tables:
    proc.kill()
    proc.wait()
    t.abort("No table widget found, cannot continue")

table = tables[0]
cols = get_table_col_count(table)
rows = get_table_row_count(table)
t.check(cols == 4,
        f"Table has 4 columns"
        if cols == 4
        else f"Expected 4 columns, got {cols}")
# 1001 from <input file> + 1 from <input> command + 1 from <item> = 1003
t.check(rows == 1003,
        f"Table has 1003 rows"
        if rows == 1003
        else f"Expected 1003 rows, got {rows}")

# --- Test 2: Default selected row ---
t.begin("testDefaultSelection")
t.check(is_row_selected(table, 1),
        "Row 1 is selected (selected-row='1')")

# --- Test 3: Disable button disables the table ---
t.begin("testDisable")
disable_btn = find_button(window, 'Disable')
if disable_btn:
    do_action(disable_btn, 'click')
    time.sleep(0.5)
    t.check(not is_enabled(table),
            "Table is disabled after Disable click")
else:
    t.check(False, "Disable button not found")

# --- Test 4: Enable button re-enables the table ---
t.begin("testEnable")
enable_btn = find_button(window, 'Enable')
if enable_btn:
    do_action(enable_btn, 'click')
    time.sleep(0.5)
    t.check(is_enabled(table),
            "Table is enabled after Enable click")
else:
    t.check(False, "Enable button not found")

# --- Test 5: Hide button hides the table ---
t.begin("testHide")
hide_btn = find_button(window, 'Hide')
if hide_btn:
    do_action(hide_btn, 'click')
    time.sleep(0.5)
    t.check(not is_showing(table),
            "Table is hidden after Hide click")
else:
    t.check(False, "Hide button not found")

# --- Test 6: Show button reveals the table ---
t.begin("testShow")
show_btn = find_button(window, 'Show')
if show_btn:
    do_action(show_btn, 'click')
    time.sleep(0.5)
    t.check(is_showing(table),
            "Table is showing after Show click")
else:
    t.check(False, "Show button not found")

# --- Test 7: Removeselected removes the selected row ---
t.begin("testRemoveSelected")
remove_btn = find_button(window, 'Removeselected')
if remove_btn:
    rows_before = get_table_row_count(table)
    do_action(remove_btn, 'click')
    time.sleep(0.5)
    rows_after = get_table_row_count(table)
    t.check(rows_after == rows_before - 1,
            f"Row removed ({rows_before} -> {rows_after})"
            if rows_after == rows_before - 1
            else f"Expected {rows_before - 1} rows, got {rows_after}")
else:
    t.check(False, "Removeselected button not found")

# --- Test 8: Clear button removes all rows ---
t.begin("testClear")
clear_btn = find_button(window, 'Clear')
if clear_btn:
    do_action(clear_btn, 'click')
    time.sleep(0.5)
    rows_after = get_table_row_count(table)
    t.check(rows_after == 0,
            "Table is empty after Clear"
            if rows_after == 0
            else f"Expected 0 rows after Clear, got {rows_after}")
else:
    t.check(False, "Clear button not found")

# --- Test 9: Refresh reloads items ---
t.begin("testRefresh")
refresh_btn = find_button(window, 'Refresh')
if refresh_btn:
    do_action(refresh_btn, 'click')
    time.sleep(2)
    rows_after = get_table_row_count(table)
    cols_after = get_table_col_count(table)
    t.check(rows_after == 1003,
            f"Table has 1003 rows after Refresh"
            if rows_after == 1003
            else f"Expected 1003 rows after Refresh, got {rows_after}")
    t.check(cols_after == 4,
            f"Table still has 4 columns after Refresh"
            if cols_after == 4
            else f"Expected 4 columns after Refresh, got {cols_after}")
else:
    t.check(False, "Refresh button not found")

# --- Test 10: Quit button closes the dialog ---
t.begin("testQuitClose")
quit_btn = find_button(window, 'Quit')
if quit_btn:
    do_action(quit_btn, 'click')
    time.sleep(1)
    retcode = proc.poll()
    if t.check(retcode is not None,
               f"Dialog closed after Quit (exit code {retcode})"
               if retcode is not None
               else "Dialog should have closed after Quit"):
        pass
    else:
        proc.kill()
        proc.wait()
else:
    t.check(False, "Quit button not found")
    proc.kill()
    proc.wait()

t.summary()

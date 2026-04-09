#!/usr/bin/env python3
"""
Automated test for examples/tree/tree using AT-SPI2.

Verifies:
1. Window appears with three tree (table) widgets
2. TREE1 (icon-column input) is populated with rows
3. TREE2 (stock-id input) is populated with rows
4. TREE3 (static items) has exactly 5 rows
5. OK button closes the dialog
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


def get_table_row_count(table):
    """Get the number of rows in a TABLE widget via its table interface."""
    ti = table.get_table_iface()
    if ti is None:
        return -1
    return ti.get_n_rows()


def get_table_col_count(table):
    """Get the number of columns in a TABLE widget via its table interface."""
    ti = table.get_table_iface()
    if ti is None:
        return -1
    return ti.get_n_columns()


def dump_tree(node, indent=0):
    """Debug helper: print the AT-SPI widget tree."""
    if node is None:
        return
    try:
        role = node.get_role_name()
        name = node.get_name() or ''
        print(f"{'  ' * indent}{role}: '{name}'")
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
t.log("Launching tree example...")
proc = subprocess.Popen(
    ['./examples/tree/tree'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

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

# Find all three tree (table) widgets
tables = find_widgets(window, Atspi.Role.TREE_TABLE)

# --- Test 1: Three trees present ---
t.begin("testThreeTrees")
t.check(len(tables) == 3,
        f"Found 3 tree widgets"
        if len(tables) == 3
        else f"Expected 3 tree widgets, found {len(tables)}")

if len(tables) < 3:
    proc.kill()
    proc.wait()
    t.abort("Not enough tree widgets found, cannot continue")

# --- Test 2: TREE1 (icon-column input) is populated ---
t.begin("testTree1Populated")
rows1 = get_table_row_count(tables[0])
cols1 = get_table_col_count(tables[0])
t.check(rows1 > 0,
        f"TREE1 has {rows1} rows"
        if rows1 > 0
        else "TREE1 is empty (0 rows)")
t.check(cols1 == 2,
        f"TREE1 has 2 columns (Permissions, Filename)"
        if cols1 == 2
        else f"TREE1: expected 2 columns, got {cols1}")

# --- Test 3: TREE2 (stock-id input) is populated ---
t.begin("testTree2Populated")
rows2 = get_table_row_count(tables[1])
cols2 = get_table_col_count(tables[1])
t.check(rows2 > 0,
        f"TREE2 has {rows2} rows"
        if rows2 > 0
        else "TREE2 is empty (0 rows)")
t.check(cols2 == 3,
        f"TREE2 has 3 columns (Icon Name, Permissions, Filename)"
        if cols2 == 3
        else f"TREE2: expected 3 columns, got {cols2}")

# --- Test 4: TREE1 and TREE2 have the same row count ---
t.begin("testTree1Tree2Match")
t.check(rows1 == rows2,
        f"TREE1 and TREE2 both have {rows1} rows"
        if rows1 == rows2
        else f"TREE1 has {rows1} rows but TREE2 has {rows2}")

# --- Test 5: TREE3 (static items) has exactly 5 rows ---
t.begin("testTree3Items")
rows3 = get_table_row_count(tables[2])
cols3 = get_table_col_count(tables[2])
t.check(rows3 == 5,
        f"TREE3 has 5 rows"
        if rows3 == 5
        else f"TREE3: expected 5 rows, got {rows3}")
t.check(cols3 == 3,
        f"TREE3 has 3 columns (Device, Directory, File)"
        if cols3 == 3
        else f"TREE3: expected 3 columns, got {cols3}")

# Verify TREE3 cell contents
t.begin("testTree3Contents")
cells3 = find_widgets(tables[2], Atspi.Role.TABLE_CELL)
cell_names = [c.get_name() or '' for c in cells3]
t.log(f"TREE3 cells: {cell_names}")
# Each row has 3 columns, so 5 rows = 15 cells
# Check for known values from the static items
t.check(any('Floppy Disk' in n for n in cell_names),
        "TREE3 contains 'Floppy Disk'")
t.check(any('CD_ROM Drive' in n for n in cell_names),
        "TREE3 contains 'CD_ROM Drive'")
t.check(any('ak.tex' in n for n in cell_names),
        "TREE3 contains 'ak.tex'")
t.check(any('/cdrom/' in n for n in cell_names),
        "TREE3 contains '/cdrom/'")

# --- Test 6: OK button closes the dialog ---
t.begin("testOkClose")
ok_btn = find_button(window, 'OK')
if ok_btn:
    do_action(ok_btn, 'click')
    time.sleep(1)
    retcode = proc.poll()
    if t.check(retcode is not None,
               f"Dialog closed after OK (exit code {retcode})"
               if retcode is not None
               else "Dialog should have closed after OK"):
        pass
    else:
        proc.kill()
        proc.wait()
else:
    t.check(False, "OK button not found")
    proc.kill()
    proc.wait()

t.summary()

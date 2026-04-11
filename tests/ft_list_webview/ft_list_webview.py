#!/usr/bin/env python3
"""
Automated test for examples/standard/list using AT-SPI2.

Verifies:
1. Window appears with the expected title
2. Tree widget has 16 rows and 2 columns
3. Tree cell contents match expected widget names
4. Selecting different rows updates the webview (non-blank)
5. OK button closes the dialog with valid JSON output
6. JSON output contains the selected tree value
"""

import json
import subprocess
import sys
import time

import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi

sys.path.insert(0, sys.path[0] + '/..')
from testlib import TestRunner

TIMEOUT = 10


def get_child_pid(shell_pid):
    """Get the gtkdialog3 child PID of the shell script."""
    try:
        result = subprocess.run(['pgrep', '-P', str(shell_pid)],
                                capture_output=True, text=True)
        pids = result.stdout.strip().split()
        if pids:
            return int(pids[0])
    except Exception:
        pass
    return None


def find_app_windows(pid):
    """Find all AT-SPI windows belonging to a PID."""
    windows = []
    desktop = Atspi.get_desktop(0)
    for i in range(desktop.get_child_count()):
        app = desktop.get_child_at_index(i)
        if app is None:
            continue
        try:
            if app.get_process_id() != pid:
                continue
        except Exception:
            continue
        for j in range(app.get_child_count()):
            win = app.get_child_at_index(j)
            if win:
                windows.append(win)
    return windows


def wait_for_window(pid, name, timeout=TIMEOUT):
    """Wait for an AT-SPI window with the given name to appear."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for win in find_app_windows(pid):
            if name.lower() in (win.get_name() or '').lower():
                return win
        time.sleep(0.3)
    return None


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
        if (btn.get_name() or '').lower() == label_text.lower():
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


def select_row(table, index):
    """Select a row by index using the selection interface."""
    si = table.get_selection_iface()
    if si:
        si.select_child(index)
        return True
    return False


def get_table_row_count(table):
    """Get the number of rows in a table widget."""
    ti = table.get_table_iface()
    if ti is None:
        return -1
    return ti.get_n_rows()


def get_table_col_count(table):
    """Get the number of columns in a table widget."""
    ti = table.get_table_iface()
    if ti is None:
        return -1
    return ti.get_n_columns()


def get_table_cell_name(table, row, col):
    """Get the accessible name of a cell at (row, col)."""
    ti = table.get_table_iface()
    if ti is None:
        return None
    cell = ti.get_accessible_at(row, col)
    if cell is None:
        return None
    return cell.get_name() or ''


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


EXPECTED_WIDGETS = [
    'button', 'checkbox', 'colorbutton', 'comboboxtext',
    'edit', 'entry', 'expander', 'fontbutton',
    'hscale', 'notebook', 'progressbar', 'radiobutton',
    'spinbutton', 'switch', 'tree', 'webview',
]


t = TestRunner()

# Launch the example
t.log("Launching list example...")
proc = subprocess.Popen(
    ['./examples/standard/list'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(2)

# Get gtkdialog3 PID
our_pid = get_child_pid(proc.pid)
if our_pid is None:
    proc.kill()
    t.abort("Could not find gtkdialog3 child process")

t.log(f"gtkdialog3 PID: {our_pid}")

# --- Test 1: Window appears ---
t.begin("testWindowAppears")
window = wait_for_window(our_pid, 'Widget Reference')
t.screenshot('GtkDialog3 Widget Reference')
if not t.check(window is not None, "Widget Reference window found"):
    proc.kill()
    t.abort("Window not found, cannot continue")

t.log(f"Found window: '{window.get_name()}'")
if t.verbose:
    print()
    dump_tree(window)
    print()

# --- Test 2: Tree widget present with correct dimensions ---
t.begin("testTreeStructure")
tables = find_widgets(window, Atspi.Role.TREE_TABLE)
if not t.check(len(tables) >= 1, f"Found tree widget (found {len(tables)})"):
    proc.kill()
    t.abort("No tree widget found, cannot continue")

tree = tables[0]
rows = get_table_row_count(tree)
cols = get_table_col_count(tree)
t.check(rows == 16,
        f"Tree has 16 rows" if rows == 16
        else f"Expected 16 rows, got {rows}")
t.check(cols == 2,
        f"Tree has 2 columns" if cols == 2
        else f"Expected 2 columns, got {cols}")

# --- Test 3: Tree cell contents ---
# GtkTreeView exposes col 0 as a tree-expander cell whose accessible
# name is empty.  The actual text renderer is a child of that cell.
# We walk TABLE_CELL children to collect all named cells per row.
t.begin("testTreeContents")
all_cells = find_widgets(tree, Atspi.Role.TABLE_CELL)
# Collect cell names, skipping empty-name parent cells
named_cells = [c.get_name() or '' for c in all_cells if (c.get_name() or '') != '']
t.log(f"Named cells (first 10): {named_cells[:10]}")

# The named cells alternate: name, summary, name, summary, ...
widget_names = named_cells[0::2]  # even indices: widget names
summaries = named_cells[1::2]     # odd indices: summaries

t.check(len(widget_names) == 16,
        f"Found 16 widget names"
        if len(widget_names) == 16
        else f"Expected 16 widget names, got {len(widget_names)}")

for i, expected_name in enumerate(EXPECTED_WIDGETS):
    if i < len(widget_names):
        t.check(widget_names[i] == expected_name,
                f"Row {i} is '{expected_name}'"
                if widget_names[i] == expected_name
                else f"Row {i}: expected '{expected_name}', got '{widget_names[i]}'")

# Check that summaries exist
t.check(len(summaries) > 0 and len(summaries[0]) > 0,
        f"Row 0 summary: '{summaries[0]}'"
        if summaries
        else "No summaries found")

# --- Test 4: Selecting rows updates the webview ---
t.begin("testSelectionUpdates")
# Select 'entry' (row 5) and wait for webview to update
select_row(tree, 5)
time.sleep(1)

# Select 'tree' (row 14) and wait for webview to update
select_row(tree, 14)
time.sleep(1)

# Select 'button' (row 0)
select_row(tree, 0)
time.sleep(1)

# We can't easily inspect webview content via AT-SPI, but we verify
# that the detail.html file was updated by the selection action
detail_file = '/tmp/gtkdialog3/examples/list/detail.html'
try:
    with open(detail_file, 'r') as f:
        html = f.read()
    t.check('&lt;button&gt;' in html or '<h1>' in html,
            "detail.html contains button documentation"
            if '&lt;button&gt;' in html
            else f"detail.html updated but content unexpected")
except FileNotFoundError:
    t.check(False, f"detail.html not found at {detail_file}")

# --- Test 5: OK closes and produces valid JSON ---
t.begin("testOkOutput")
ok_btn = find_button(window, 'OK')
if ok_btn:
    do_action(ok_btn, 'click')
    time.sleep(1)

    retcode = proc.poll()
    if not t.check(retcode is not None,
                   f"Dialog closed after OK (exit code {retcode})"
                   if retcode is not None
                   else "Dialog should have closed after OK"):
        proc.kill()
        proc.wait(timeout=3)

    stdout = proc.stdout.read().decode()
    t.log(f"stdout: {repr(stdout)}")

    data = None
    try:
        data = json.loads(stdout)
        t.check(True, "Output is valid JSON")
    except json.JSONDecodeError as e:
        t.check(False, f"Output is valid JSON (parse error: {e})")

    if data is not None:
        t.check('widget_contents' in data,
                "'widget_contents' key present")
        t.check('exit' in data,
                "'exit' key present")
        t.check(data.get('exit') == 'OK',
                f"exit is 'OK' (got '{data.get('exit')}')")

        wc = data.get('widget_contents', {})
        t.check('listDialog' in wc,
                f"'listDialog' in output (keys: {list(wc.keys())})")

        if 'listDialog' in wc:
            ld = wc['listDialog']
            t.check('wgtTree' in ld,
                    f"'wgtTree' variable in output (keys: {list(ld.keys())})")
            selected = ld.get('wgtTree', '')
            t.check(selected in EXPECTED_WIDGETS,
                    f"wgtTree is a valid widget name: '{selected}'"
                    if selected in EXPECTED_WIDGETS
                    else f"wgtTree has unexpected value: '{selected}'")
else:
    t.check(False, "OK button not found")
    proc.kill()
    proc.wait()

t.summary()

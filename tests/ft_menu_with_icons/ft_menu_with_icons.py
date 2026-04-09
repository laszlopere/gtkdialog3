#!/usr/bin/env python3
"""
Automated test for examples/menu/menu_with_icons using AT-SPI2.

Verifies:
1. Window appears with expected title
2. Menu bar with File and Edit menus is present
3. All menu items are present with correct labels
4. Clicking menu items prints correct action IDs to stdout
5. Quit menu item closes the dialog with EXIT="Quit"
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


def find_widget_by_name(node, role, name):
    """Find a widget by role and name."""
    for w in find_widgets(node, role):
        if (w.get_name() or '') == name:
            return w
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


def click_menu_item(window, menu_name, item_name):
    """Open a menu by name, then click an item within it.
    Uses mouse events so the highlight visually tracks the pointer."""
    menu = find_widget_by_name(window, Atspi.Role.MENU, menu_name)
    if menu is None:
        return False
    do_action(menu, 'click')
    time.sleep(0.3)
    item = find_widget_by_name(window, Atspi.Role.MENU_ITEM, item_name)
    if item is None:
        return False
    # Move pointer to the center of the menu item to trigger highlight.
    # The abs warp alone doesn't generate GTK motion events, so a small
    # relative nudge is needed to make the highlight follow the cursor.
    comp = item.get_component_iface()
    if comp:
        rect = comp.get_extents(Atspi.CoordType.SCREEN)
        cx = rect.x + rect.width // 2
        cy = rect.y + rect.height // 2
        Atspi.generate_mouse_event(cx, cy, 'abs')
        time.sleep(0.05)
        Atspi.generate_mouse_event(1, 0, 'rel')
        time.sleep(0.05)
        Atspi.generate_mouse_event(-1, 0, 'rel')
        time.sleep(0.3)
        Atspi.generate_mouse_event(cx, cy, 'b1c')
    else:
        do_action(item, 'click')
    time.sleep(0.5)
    return True


t = TestRunner()

# Launch the example
t.log("Launching menu_with_icons example...")
proc = subprocess.Popen(
    ['./examples/menu/menu_with_icons'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('Menu With Icons')

if window is None:
    proc.kill()
    t.abort("Could not find Menu With Icons window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")

# Gather widgets
menus = find_widgets(window, Atspi.Role.MENU)
items = find_widgets(window, Atspi.Role.MENU_ITEM)
menu_bar = find_widgets(window, Atspi.Role.MENU_BAR)
t.log(f"Found {len(menus)} menus, {len(items)} items")

# --- Test 1: Widget presence ---
t.begin("testWidgetPresence")
t.check('Menu With Icons' in (window.get_name() or ''),
        "Window title is 'Menu With Icons'")
t.check(len(menu_bar) == 1, "Menu bar is present")

menu_names = [m.get_name() or '' for m in menus]
t.check('File' in menu_names, "File menu is present")
t.check('Edit' in menu_names, "Edit menu is present")

# --- Test 2: File menu items ---
t.begin("testFileMenuItems")
file_items = ['New', 'Open', 'Save', 'Print', 'Close Other Documents', 'Quit']
for name in file_items:
    t.check(find_widget_by_name(window, Atspi.Role.MENU_ITEM, name) is not None,
            f"File menu has '{name}' item")

# --- Test 3: Edit menu items ---
t.begin("testEditMenuItems")
edit_items = ['Undo', 'Redo', 'Cut', 'Copy', 'Paste', 'Delete', 'Select All']
for name in edit_items:
    t.check(find_widget_by_name(window, Atspi.Role.MENU_ITEM, name) is not None,
            f"Edit menu has '{name}' item")

# --- Test 4: Menu item actions print correct IDs ---
t.begin("testMenuActions")
test_clicks = [
    ('File', 'New', 'file:new'),
    ('File', 'Open', 'file:open'),
    ('File', 'Save', 'file:save'),
    ('File', 'Print', 'file:print'),
    ('File', 'Close Other Documents', 'file:close-other'),
    ('Edit', 'Undo', 'edit:undo'),
    ('Edit', 'Redo', 'edit:redo'),
    ('Edit', 'Cut', 'edit:cut'),
    ('Edit', 'Copy', 'edit:copy'),
    ('Edit', 'Paste', 'edit:paste'),
    ('Edit', 'Delete', 'edit:delete'),
    ('Edit', 'Select All', 'edit:select-all'),
]
for menu_name, item_name, expected_output in test_clicks:
    t.log(f"Clicking {menu_name} > {item_name}...")
    click_menu_item(window, menu_name, item_name)

# --- Test 5: Quit closes the dialog ---
t.begin("testQuit")
click_menu_item(window, 'File', 'Quit')
time.sleep(1)

retcode = proc.poll()
if t.check(retcode is not None,
           f"Dialog closed after Quit (exit code {retcode})"
           if retcode is not None
           else "Dialog should have closed after Quit"):
    stdout = proc.stdout.read().decode()
    t.log(f"stdout: {repr(stdout)}")

    for menu_name, item_name, expected_output in test_clicks:
        t.check(expected_output in stdout,
                f"'{expected_output}' found in output")
    t.check('EXIT="Quit"' in stdout,
            "EXIT is 'Quit' in output")
else:
    proc.kill()

t.summary()

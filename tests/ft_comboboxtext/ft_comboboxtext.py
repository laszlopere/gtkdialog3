#!/usr/bin/env python3
"""
Automated test for examples/comboboxtext/comboboxtext_advanced using AT-SPI2.

Launches the comboboxtext_advanced example and verifies:
1. Window appears with deprecated combobox and comboboxtext panels
2. Each deprecated combobox variant: items, Clear, Refresh
3. Each comboboxtext variant: initial value, items, select, Delete,
   Clear, Refresh, Save, Disable, Enable
4. Clicking OK closes the dialog
"""

import os
import subprocess
import sys
import time
import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi

sys.path.insert(0, sys.path[0] + '/..')
from testlib import TestRunner

TIMEOUT = 10  # seconds
OUTPUTFILE = '/tmp/gtkdialog3/examples/comboboxtext_advanced/outputfile'


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
        sensitive = states.contains(Atspi.StateType.SENSITIVE)
        print(f"{'  ' * indent}{role}: '{name}' sensitive={sensitive}")
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


def is_sensitive(widget):
    """Check if a widget is sensitive/enabled."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.SENSITIVE)


def get_menu_items(combo):
    """Get menu item names from a combo box."""
    menus = find_widgets(combo, Atspi.Role.MENU)
    if not menus:
        return []
    items = find_widgets(menus[0], Atspi.Role.MENU_ITEM)
    return [it.get_name() or '' for it in items]


def get_menu_item_widgets(combo):
    """Get menu item AT-SPI nodes from a combo box."""
    menus = find_widgets(combo, Atspi.Role.MENU)
    if not menus:
        return []
    return find_widgets(menus[0], Atspi.Role.MENU_ITEM)


def find_button(buttons, name):
    """Find a button by name in a list."""
    for b in buttons:
        if b.get_name() == name:
            return b
    return None


def click(button):
    """Click a button and wait for the action to take effect."""
    do_action(button, 'click')
    time.sleep(0.5)


t = TestRunner()

# Clean up output file from previous runs
if os.path.exists(OUTPUTFILE):
    os.remove(OUTPUTFILE)

# Launch the comboboxtext_advanced example
t.log("Launching comboboxtext_advanced example...")
proc = subprocess.Popen(
    ['./examples/comboboxtext/comboboxtext_advanced'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('ComboBoxText Advanced')

if window is None:
    proc.kill()
    t.abort("Could not find ComboBoxText Advanced window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")
if t.verbose:
    print()
    print("Widget tree:")
    dump_tree(window)
    print()

# Find the two framed panels
panels = find_widgets(window, Atspi.Role.PANEL)
deprecated_panel = None
comboboxtext_panel = None
for p in panels:
    name = (p.get_name() or '').lower()
    if 'deprecated' in name:
        deprecated_panel = p
    elif 'comboboxtext' in name:
        comboboxtext_panel = p

# --- Test 1: Initial structure ---
t.begin("testInitialState")

t.check(deprecated_panel is not None, "Deprecated combobox panel found")
t.check(comboboxtext_panel is not None, "Comboboxtext panel found")

all_combos = find_widgets(window, Atspi.Role.COMBO_BOX)
t.check(len(all_combos) == 6, f"Found 6 combo boxes total (got {len(all_combos)})")

all_buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
ok_button = find_button(all_buttons, 'OK')
t.check(ok_button is not None, "OK button found")

t.screenshot("ComboBoxText Advanced")

# --- Test 2: Deprecated combo 0 (no tag attributes) ---
t.begin("testDepCombo0")

dep_combos = find_widgets(deprecated_panel, Atspi.Role.COMBO_BOX)
dep_buttons = find_widgets(deprecated_panel, Atspi.Role.PUSH_BUTTON)
# Buttons are ordered: [Clear0, Refresh0, Clear1, Refresh1, Clear2, Refresh2]

if t.check(len(dep_combos) >= 3, f"Deprecated panel has 3 combos (got {len(dep_combos)})"):
    items = get_menu_items(dep_combos[0])
    t.check(items == ['cboComboBox0', 'tag attributes none'],
            f"Combo 0 items correct (got {items})")

    # Clear
    click(find_button(dep_buttons[0:2], 'Clear'))
    t.check(get_menu_items(dep_combos[0]) == [], "Combo 0 cleared")

    # Refresh
    click(find_button(dep_buttons[0:2], 'Refresh'))
    items = get_menu_items(dep_combos[0])
    t.check(items == ['cboComboBox0', 'tag attributes none'],
            f"Combo 0 refreshed (got {items})")

# --- Test 3: Deprecated combo 1 (allow-empty=false, value-in-list=true) ---
t.begin("testDepCombo1")

if len(dep_combos) >= 3:
    items = get_menu_items(dep_combos[1])
    t.check(len(items) == 3, f"Combo 1 has 3 items (got {len(items)})")
    t.check('cboComboBox1' in items, "Combo 1 has 'cboComboBox1'")
    t.check('tag attribute allow-empty="false"' in items,
            "Combo 1 has allow-empty item")
    t.check('tag attribute value-in-list="true"' in items,
            "Combo 1 has value-in-list item")

    # Clear
    click(find_button(dep_buttons[2:4], 'Clear'))
    t.check(get_menu_items(dep_combos[1]) == [], "Combo 1 cleared")

    # Refresh
    click(find_button(dep_buttons[2:4], 'Refresh'))
    items = get_menu_items(dep_combos[1])
    t.check(len(items) == 3, f"Combo 1 refreshed (got {len(items)} items)")

# --- Test 4: Deprecated combo 2 (case-sensitive=true, value-in-list=true) ---
t.begin("testDepCombo2")

if len(dep_combos) >= 3:
    items = get_menu_items(dep_combos[2])
    t.check(len(items) == 3, f"Combo 2 has 3 items (got {len(items)})")
    t.check('cboComboBox2' in items, "Combo 2 has 'cboComboBox2'")
    t.check('tag attribute case-sensitive="true"' in items,
            "Combo 2 has case-sensitive item")

    # Clear
    click(find_button(dep_buttons[4:6], 'Clear'))
    t.check(get_menu_items(dep_combos[2]) == [], "Combo 2 cleared")

    # Refresh
    click(find_button(dep_buttons[4:6], 'Refresh'))
    items = get_menu_items(dep_combos[2])
    t.check(len(items) == 3, f"Combo 2 refreshed (got {len(items)} items)")

# --- Test 5: ComboBoxText 0 (fs-action=file) ---
t.begin("testCBText0")

cbt_combos = find_widgets(comboboxtext_panel, Atspi.Role.COMBO_BOX)
cbt_buttons = find_widgets(comboboxtext_panel, Atspi.Role.PUSH_BUTTON)
# Each comboboxtext has 7 buttons: Clear, Delete, Refresh, Save, Disable, Enable, Fileselect
btns0 = cbt_buttons[0:7]

if t.check(len(cbt_combos) >= 3, f"ComboBoxText panel has 3 combos (got {len(cbt_combos)})"):
    combo = cbt_combos[0]

    # Initial value and items
    t.check(combo.get_name() == 'This came from a shell command',
            f"CBText 0 initial value (got '{combo.get_name()}')")
    items = get_menu_items(combo)
    t.check('This came from a shell command' in items, "CBText 0 has shell command item")
    t.check('This came from an input file' in items, "CBText 0 has input file item")
    t.check('cboComboBoxText0' in items, "CBText 0 has variable name item")
    t.check("tag attribute fs-action='file'" in items, "CBText 0 has fs-action item")
    orig_count = len(items)

    # Select a different item
    mi = get_menu_item_widgets(combo)
    if len(mi) >= 3:
        do_action(mi[2])  # select 'cboComboBoxText0'
        time.sleep(0.5)
        t.check(combo.get_name() == 'cboComboBoxText0',
                f"CBText 0 selected item 2 (got '{combo.get_name()}')")

    # Delete removes selected item
    click(find_button(btns0, 'Delete'))
    items = get_menu_items(combo)
    t.check('cboComboBoxText0' not in items, "CBText 0 deleted selected item")
    t.check(len(items) == orig_count - 1,
            f"CBText 0 item count reduced (got {len(items)})")

    # Clear removes all items
    click(find_button(btns0, 'Clear'))
    t.check(get_menu_items(combo) == [], "CBText 0 cleared all items")

    # Refresh reloads items
    click(find_button(btns0, 'Refresh'))
    items = get_menu_items(combo)
    t.check(len(items) == orig_count, f"CBText 0 refreshed (got {len(items)} items)")
    t.check(combo.get_name() == 'This came from a shell command',
            f"CBText 0 value after refresh (got '{combo.get_name()}')")

    # Save writes items to output file
    click(find_button(btns0, 'Save'))
    t.check(os.path.exists(OUTPUTFILE), "CBText 0 Save created output file")
    if os.path.exists(OUTPUTFILE):
        content = open(OUTPUTFILE).read().strip()
        t.check('This came from a shell command' in content,
                "Output file contains shell command item")

    # Disable / Enable
    t.check(is_sensitive(combo), "CBText 0 is sensitive initially")
    click(find_button(btns0, 'Disable'))
    t.check(not is_sensitive(combo), "CBText 0 insensitive after Disable")
    click(find_button(btns0, 'Enable'))
    t.check(is_sensitive(combo), "CBText 0 sensitive after Enable")

# --- Test 6: ComboBoxText 1 (active=4, button-sensitivity=1) ---
t.begin("testCBText1")

btns1 = cbt_buttons[7:14]

if len(cbt_combos) >= 2:
    combo = cbt_combos[1]

    # Initial value: active="4" selects 5th item (0-indexed)
    t.check(combo.get_name() == 'tag attribute active="4"',
            f"CBText 1 initial value from active index (got '{combo.get_name()}')")
    items = get_menu_items(combo)
    t.check('cboComboBoxText1' in items, "CBText 1 has variable name item")
    t.check('tag attribute button-sensitivity="1"' in items,
            "CBText 1 has button-sensitivity item")
    t.check(len(items) == 7, f"CBText 1 has 7 items (got {len(items)})")
    orig_count = len(items)

    # Select a different item
    mi = get_menu_item_widgets(combo)
    if len(mi) >= 1:
        do_action(mi[0])  # select first item
        time.sleep(0.5)
        t.check(combo.get_name() == 'This came from a shell command',
                f"CBText 1 selected item 0 (got '{combo.get_name()}')")

    # Delete
    click(find_button(btns1, 'Delete'))
    items = get_menu_items(combo)
    t.check(len(items) == orig_count - 1,
            f"CBText 1 item count after delete (got {len(items)})")

    # Clear
    click(find_button(btns1, 'Clear'))
    t.check(get_menu_items(combo) == [], "CBText 1 cleared")

    # Refresh
    click(find_button(btns1, 'Refresh'))
    items = get_menu_items(combo)
    t.check(len(items) == orig_count, f"CBText 1 refreshed (got {len(items)} items)")

    # Save
    if os.path.exists(OUTPUTFILE):
        os.remove(OUTPUTFILE)
    click(find_button(btns1, 'Save'))
    t.check(os.path.exists(OUTPUTFILE), "CBText 1 Save created output file")

    # Disable / Enable
    click(find_button(btns1, 'Disable'))
    t.check(not is_sensitive(combo), "CBText 1 insensitive after Disable")
    click(find_button(btns1, 'Enable'))
    t.check(is_sensitive(combo), "CBText 1 sensitive after Enable")

# --- Test 7: ComboBoxText 2 (focus-on-click=false) ---
t.begin("testCBText2")

btns2 = cbt_buttons[14:21]

if len(cbt_combos) >= 3:
    combo = cbt_combos[2]

    # Initial value: default directive text
    name = combo.get_name() or ''
    t.check('default directive' in name.lower(),
            f"CBText 2 shows default directive (got '{name}')")
    items = get_menu_items(combo)
    t.check('cboComboBoxText2' in items, "CBText 2 has variable name item")
    t.check('tag attribute focus-on-click="false"' in items,
            "CBText 2 has focus-on-click item")
    orig_count = len(items)

    # Select a different item
    mi = get_menu_item_widgets(combo)
    if len(mi) >= 2:
        do_action(mi[1])  # select 'This came from an input file'
        time.sleep(0.5)
        t.check(combo.get_name() == 'This came from an input file',
                f"CBText 2 selected item 1 (got '{combo.get_name()}')")

    # Delete
    click(find_button(btns2, 'Delete'))
    items = get_menu_items(combo)
    t.check(len(items) == orig_count - 1,
            f"CBText 2 item count after delete (got {len(items)})")

    # Clear
    click(find_button(btns2, 'Clear'))
    t.check(get_menu_items(combo) == [], "CBText 2 cleared")

    # Refresh
    click(find_button(btns2, 'Refresh'))
    items = get_menu_items(combo)
    t.check(len(items) == orig_count, f"CBText 2 refreshed (got {len(items)} items)")

    # Save
    if os.path.exists(OUTPUTFILE):
        os.remove(OUTPUTFILE)
    click(find_button(btns2, 'Save'))
    t.check(os.path.exists(OUTPUTFILE), "CBText 2 Save created output file")

    # Disable / Enable
    click(find_button(btns2, 'Disable'))
    t.check(not is_sensitive(combo), "CBText 2 insensitive after Disable")
    click(find_button(btns2, 'Enable'))
    t.check(is_sensitive(combo), "CBText 2 sensitive after Enable")

# --- Test 8: Close via OK ---
t.begin("testCloseDialog")

if t.check(ok_button is not None, "OK button found"):
    do_action(ok_button, 'click')
    time.sleep(1)

    retcode = proc.poll()
    if not t.check(retcode is not None,
                   f"Dialog closed after OK click (exit code {retcode})"
                   if retcode is not None
                   else "Dialog should have closed after OK click"):
        proc.kill()
else:
    proc.kill()

t.summary()

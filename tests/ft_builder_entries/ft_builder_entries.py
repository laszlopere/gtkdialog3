#!/usr/bin/env python3
"""
Automated test for examples/builder/builder-entries_functions using AT-SPI.

This tests the GtkBuilder UI file support (--ui-file).  Verifies:
1. The window loads from a .ui file and appears with the expected widgets
2. Three entry fields are present
3. Server entry has the default value "localhost"
4. Name entry is populated by the realize handler (whoami)
5. OK and Cancel buttons exist
6. Typing into an entry works
7. Clicking Cancel closes the dialog and exports variable values
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

TIMEOUT = 10
PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..'))


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


def get_text(widget):
    """Get the text content of a widget via AT-SPI."""
    return Atspi.Text.get_text(widget, 0, -1)


t = TestRunner()

# Launch the builder entries example
t.log("Launching builder-entries_functions example...")
proc = subprocess.Popen(
    ['./examples/builder/builder-entries_functions.sh'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=PROJECT_ROOT
)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('GtkDialog Example')
t.screenshot('GtkDialog Example')

if window is None:
    proc.kill()
    t.abort("Could not find GtkDialog Example window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")

# Find all entry fields and buttons
entries = find_widgets(window, Atspi.Role.TEXT)
if not entries:
    entries = find_widgets(window, Atspi.Role.ENTRY)
buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)

# Identify entries by content (AT-SPI order may differ from UI file order)
expected_user = os.environ.get('USER', '')
server_entry = None
name_entry = None
db_entry = None
for e in entries:
    text = get_text(e)
    if text == 'localhost':
        server_entry = e
    elif text == expected_user:
        name_entry = e
    elif text == '':
        db_entry = e

# --- Test 1: Window and widgets present ---
t.begin("testWidgetsPresent")
t.check(window.get_name() == 'GtkDialog Example',
        f"Window title is 'GtkDialog Example' (got '{window.get_name()}')")
t.check(len(entries) == 3,
        f"3 entry fields found (got {len(entries)})")
t.check(len(buttons) == 2,
        f"2 buttons found (got {len(buttons)})")

# --- Test 2: Default values ---
t.begin("testDefaultValues")
t.check(server_entry is not None,
        f"Server entry found with value 'localhost'")
t.check(name_entry is not None,
        f"Name entry populated by realize handler (whoami): '{expected_user}'")
t.check(db_entry is not None,
        "Database entry is empty")

# --- Test 3: Type a value into the database entry ---
t.begin("testEditEntry")
if db_entry is not None:
    ei = db_entry.get_editable_text_iface()
    if ei:
        Atspi.EditableText.insert_text(ei, 0, 'mydb', len('mydb'))
        time.sleep(0.3)
        db_text = get_text(db_entry)
        t.check(db_text == 'mydb',
                f"Database entry now 'mydb' (got '{db_text}')")
    else:
        t.check(False, "Could not get editable text interface")
else:
    t.check(False, "Database entry not found")

# --- Test 4: Click Cancel to close the dialog ---
t.begin("testCancelCloses")
cancel_button = None
for b in buttons:
    bname = (b.get_name() or '').lower()
    if 'cancel' in bname:
        cancel_button = b
        break

if cancel_button:
    do_action(cancel_button, 'click')
    time.sleep(1)

    retcode = proc.poll()
    if not t.check(retcode is not None,
                   f"Dialog closed after Cancel click (exit code {retcode})"
                   if retcode is not None
                   else "Dialog should have closed after Cancel click"):
        proc.kill()
        proc.wait(timeout=3)

    stdout = proc.stdout.read().decode()
    t.log(f"stdout: {repr(stdout)}")

    t.check('server_entry="localhost"' in stdout,
            "Output exports server_entry=\"localhost\"")
    t.check('database_entry="mydb"' in stdout,
            "Output exports database_entry=\"mydb\"")
    t.check(f'name_entry="{expected_user}"' in stdout,
            f"Output exports name_entry=\"{expected_user}\"")
    t.check('EXIT="Cancel"' in stdout,
            "Output exports EXIT=\"Cancel\"")
else:
    t.check(False, "Cancel button not found")
    proc.kill()

t.summary()

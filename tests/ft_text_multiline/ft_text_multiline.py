#!/usr/bin/env python3
"""
Automated test for examples/text/text_multiline using AT-SPI2.

Verifies:
1. The window appears with the expected title
2. Plain multi-line label is present with full text
3. Centre-justified multi-line label is present
4. Markup multi-line label is present with formatted text
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

TIMEOUT = 10


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


def find_label_containing(labels, text):
    """Find a label whose name contains the given text."""
    for lbl in labels:
        name = lbl.get_name() or ''
        if text.lower() in name.lower():
            return lbl
    return None


t = TestRunner()

# Launch the example
t.log("Launching text_multiline example...")
proc = subprocess.Popen(
    ['./examples/text/text_multiline'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('Multi-line Label Demo')
t.screenshot('Multi-line Label Demo')

if window is None:
    proc.kill()
    t.abort("Could not find Multi-line Label Demo window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")

# Gather all labels
labels = find_widgets(window, Atspi.Role.LABEL)
t.log(f"Found {len(labels)} labels")

# --- Test 1: Window title ---
t.begin("testWindowTitle")
t.check('multi-line label demo' in (window.get_name() or '').lower(),
        "Window title is 'Multi-line Label Demo'")

# --- Test 2: Plain multi-line label ---
t.begin("testPlainLabel")
plain = find_label_containing(labels, 'GtkDialog allows you to build')
t.check(plain is not None, "Plain multi-line label is present")
if plain:
    name = plain.get_name() or ''
    t.check('markup language' in name,
            "Label contains text from second line")
    t.check('without writing any C code' in name,
            "Label contains text from last line")

# --- Test 3: Centre-justified multi-line label ---
t.begin("testCentreLabel")
centre = find_label_containing(labels, 'justification modes')
t.check(centre is not None, "Centre-justified label is present")
if centre:
    name = centre.get_name() or ''
    t.check('centre-justified' in name,
            "Label contains text from second line")
    t.check('space of the window' in name,
            "Label contains text from last line")

# --- Test 4: Markup multi-line label ---
t.begin("testMarkupLabel")
markup = find_label_containing(labels, 'Pango markup')
t.check(markup is not None, "Markup multi-line label is present")
if markup:
    name = markup.get_name() or ''
    t.check('underline important' in name,
            "Label contains text from middle line")
    t.check('parts of the message' in name,
            "Label contains text from last line")

# --- Test 5: OK button closes dialog ---
t.begin("testOkClose")
buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
ok_button = None
for b in buttons:
    name = (b.get_name() or '').lower()
    if 'ok' in name or 'gtk-ok' in name:
        ok_button = b
        break
if ok_button is None and buttons:
    ok_button = buttons[0]

if ok_button:
    do_action(ok_button, 'click')
    time.sleep(1)
    retcode = proc.poll()
    if t.check(retcode is not None,
               f"Dialog closed after OK click (exit code {retcode})"
               if retcode is not None
               else "Dialog should have closed after OK click"):
        pass
    else:
        proc.kill()
else:
    t.check(False, "OK button not found")
    proc.kill()

t.summary()

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
from testlib import TestRunner, launch, wait_for_window, unique_app_name

TIMEOUT = 10


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
APP_NAME = unique_app_name()
proc = launch(['./examples/text/text_multiline'], APP_NAME)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window(APP_NAME, 'Multi-line Label Demo')
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

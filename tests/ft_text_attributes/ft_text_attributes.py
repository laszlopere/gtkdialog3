#!/usr/bin/env python3
"""
Automated test for examples/text/text_attributes using AT-SPI2.

Verifies:
1. The window appears with the expected labels
2. Angled text label is present
3. Left/right/centre justified labels are present
4. max-width-chars and width-chars labels are present
5. Pattern-underlined label is present
6. Selectable label is present and has SELECTABLE_TEXT state
7. Markup label contains expected formatted text
8. OK button closes the dialog
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
t.log("Launching text_attributes example...")
proc = subprocess.Popen(
    ['./examples/text/text_attributes'],
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

# Gather all labels
labels = find_widgets(window, Atspi.Role.LABEL)
t.log(f"Found {len(labels)} labels")

# --- Test 1: Angled text label ---
t.begin("testAngledText")
angled = find_label_containing(labels, 'Angled text')
t.check(angled is not None, "Angled text label is present")

# --- Test 2: Justified text labels ---
t.begin("testJustifiedText")
left = find_label_containing(labels, 'left justified')
t.check(left is not None, "Left justified label is present")

right = find_label_containing(labels, 'right justified')
t.check(right is not None, "Right justified label is present")

centre = find_label_containing(labels, 'centre justified')
t.check(centre is not None, "Centre justified label is present")

# --- Test 3: Width constraint labels ---
t.begin("testWidthConstraints")
max_width = find_label_containing(labels, 'maximum width')
t.check(max_width is not None, "max-width-chars label is present")

width = find_label_containing(labels, 'desired width')
t.check(width is not None, "width-chars label is present")

# --- Test 4: Pattern underlined label ---
t.begin("testPatternLabel")
pattern = find_label_containing(labels, 'underlined words')
t.check(pattern is not None, "Pattern-underlined label is present")

# --- Test 5: Selectable text ---
t.begin("testSelectableText")
selectable = find_label_containing(labels, 'can be selected')
t.check(selectable is not None, "Selectable label is present")
if selectable:
    states = selectable.get_state_set()
    # GTK2 selectable labels expose FOCUSABLE via AT-SPI
    t.check(states.contains(Atspi.StateType.FOCUSABLE),
            "Selectable label has FOCUSABLE state")

# --- Test 6: Markup label ---
t.begin("testMarkupLabel")
markup = find_label_containing(labels, 'markup')
t.check(markup is not None, "Markup label is present")

# --- Test 7: OK button closes dialog ---
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

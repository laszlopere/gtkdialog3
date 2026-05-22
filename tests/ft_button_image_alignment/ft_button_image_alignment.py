#!/usr/bin/env python3
"""
Automated test for examples/button/button_image_horizontal_alignment
using AT-SPI2.

Verifies:
1. Window appears with expected title
2. Descriptive text labels are present for each column
3. All 20 icon buttons and the Quit button are present
4. Clicking icon buttons prints their stock name to stdout
5. Quit button closes the dialog with EXIT="abort"
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

STOCK_ICONS = [
    'gtk-print',
    'gtk-orientation-landscape',
    'gtk-undelete',
    'gtk-select-color',
    'gtk-cut',
]


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


def click_button_visually(button):
    """Click a button using mouse events so the press is visible."""
    comp = button.get_component_iface()
    if comp:
        rect = comp.get_extents(Atspi.CoordType.SCREEN)
        cx = rect.x + rect.width // 2
        cy = rect.y + rect.height // 2
        Atspi.generate_mouse_event(cx, cy, 'abs')
        time.sleep(0.05)
        Atspi.generate_mouse_event(1, 0, 'rel')
        time.sleep(0.05)
        Atspi.generate_mouse_event(-1, 0, 'rel')
        time.sleep(0.15)
        Atspi.generate_mouse_event(cx, cy, 'b1c')
    else:
        do_action(button, 'click')
    time.sleep(0.3)


t = TestRunner()

# Launch the example
t.log("Launching button_image_horizontal_alignment example...")
proc = subprocess.Popen(
    ['./examples/button/button_image_horizontal_alignment'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('Button Image Horizontal Alignment')
t.screenshot('Button Image Horizontal Alignment')

if window is None:
    proc.kill()
    t.abort("Could not find 'Button Image Horizontal Alignment' window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")

# Gather widgets
buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
labels = find_widgets(window, Atspi.Role.LABEL)
separators = find_widgets(window, Atspi.Role.SEPARATOR)

button_names = [b.get_name() or '' for b in buttons]
label_texts = [l.get_name() or '' for l in labels]

t.log(f"Found {len(buttons)} buttons, {len(labels)} labels, {len(separators)} separators")

# --- Test 1: Window and layout ---
t.begin("testWidgetPresence")
t.check('Button Image Horizontal Alignment' in (window.get_name() or ''),
        "Window title is correct")
# 20 icon buttons + 1 Quit button = 21
t.check(len(buttons) == 21,
        f"21 buttons present (got {len(buttons)})")
t.check(len(separators) >= 2,
        f"At least 2 separators present (got {len(separators)})")

# --- Test 2: Descriptive column labels ---
t.begin("testColumnLabels")
expected_labels = [
    '<button>',
    "<button homogeneous='true'>",
    "<button image-position='1'>",
    "<button image-position='1' homogeneous='true'>",
]
for expected in expected_labels:
    t.check(expected in label_texts,
            f"Column label '{expected}' is present")

# --- Test 3: All icon buttons are present ---
t.begin("testIconButtons")
for icon in STOCK_ICONS:
    count = button_names.count(icon)
    t.check(count == 4,
            f"'{icon}' appears 4 times (got {count})")

t.check('Quit' in button_names, "Quit button is present")

# --- Test 4: Click one button from each column and verify output ---
t.begin("testButtonActions")
# Click the first icon in each of the 4 columns.
# Each column has the same 5 icons; we click the distinct ones to
# get 4 separate echo lines (all "gtk-print").  Instead, click one
# unique icon per column so the output lines are distinguishable.
click_icons = ['gtk-print', 'gtk-orientation-landscape', 'gtk-undelete', 'gtk-select-color']
for icon in click_icons:
    btn = find_widget_by_name(window, Atspi.Role.PUSH_BUTTON, icon)
    if btn:
        t.log(f"Clicking '{icon}'...")
        click_button_visually(btn)

# --- Test 5: Quit closes the dialog ---
t.begin("testQuitButton")
quit_btn = find_widget_by_name(window, Atspi.Role.PUSH_BUTTON, 'Quit')
if quit_btn:
    t.log("Clicking Quit...")
    click_button_visually(quit_btn)
    time.sleep(1)

    retcode = proc.poll()
    if t.check(retcode is not None,
               f"Dialog closed after Quit (exit code {retcode})"
               if retcode is not None
               else "Dialog should have closed after Quit"):
        stdout = proc.stdout.read().decode()
        t.log(f"stdout: {repr(stdout)}")

        for icon in click_icons:
            t.check(icon in stdout,
                    f"'{icon}' found in output")
        t.check('EXIT="Quit"' in stdout,
                "EXIT is 'Quit' in output")
    else:
        proc.kill()
else:
    t.check(False, "Quit button not found")
    proc.kill()

t.summary()

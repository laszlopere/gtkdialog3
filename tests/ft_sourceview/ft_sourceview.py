#!/usr/bin/env python3
"""
Automated test for examples/standard/sourceview using AT-SPI.

Verifies:
1. Window appears with the expected title
2. Language buttons (C Program, JSON Data, Bash Script) and OK button are present
3. Clicking Bash Script button loads bash content into the editor
4. Clicking OK produces valid JSON output with correct window/variable keys
"""

import json
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


def find_button_by_label(window, label_text):
    """Find a button by its label text (exact match)."""
    for btn in find_widgets(window, Atspi.Role.PUSH_BUTTON):
        if (btn.get_name() or '').lower() == label_text.lower():
            return btn
    return None


def get_editor_text(window):
    """Get text from the sourceview/text editor widget."""
    for w in find_widgets(window, Atspi.Role.TEXT):
        ti = w.get_text_iface()
        if ti:
            text = Atspi.Text.get_text(ti, 0, -1)
            if text and len(text) > 10:
                return text
    return None


t = TestRunner()

# Launch the example
t.log("Launching sourceview example...")
APP_NAME = unique_app_name()
proc = launch(['./examples/standard/sourceview'], APP_NAME)

time.sleep(2)

# --- Test 1: Window and buttons appear ---
t.begin("testWindowAppears")
app, window = wait_for_window(APP_NAME, 'Source Code Viewer')
t.screenshot('Source Code Viewer')
if not t.check(window is not None, "Source Code Viewer window found"):
    proc.kill()
    t.summary()

btn_c = find_button_by_label(window, 'C Program')
btn_json = find_button_by_label(window, 'JSON Data')
btn_bash = find_button_by_label(window, 'Bash Script')
btn_ok = find_button_by_label(window, 'OK')

t.check(btn_c is not None, "'C Program' button found")
t.check(btn_json is not None, "'JSON Data' button found")
t.check(btn_bash is not None, "'Bash Script' button found")
t.check(btn_ok is not None, "'OK' button found")

# --- Test 2: Click Bash Script and verify content ---
t.begin("testBashContent")
if btn_bash:
    btn_bash.get_action_iface().do_action(0)
    time.sleep(1)

    text = get_editor_text(window)
    t.check(text is not None, "Editor text is readable")
    if text:
        t.check('#!/bin/bash' in text,
                "Editor contains bash shebang")
        t.check('usage()' in text,
                "Editor contains bash function")

# --- Test 3: Click OK and verify JSON output ---
t.begin("testJsonOutput")
if btn_ok:
    btn_ok.get_action_iface().do_action(0)
    time.sleep(1)

    retcode = proc.poll()
    if not t.check(retcode is not None,
                   f"Dialog closed after OK (exit code {retcode})"
                   if retcode is not None
                   else "Dialog should have closed after OK"):
        proc.kill()
        proc.wait(timeout=3)

    stdout = proc.stdout.read().decode()
    t.log(f"stdout: {repr(stdout[:200])}")

    data = None
    try:
        data = json.loads(stdout)
        t.check(True, "Output is valid JSON")
    except json.JSONDecodeError as e:
        t.check(False, f"Output is valid JSON (parse error: {e})")

    if data is not None:
        t.check('widget_contents' in data,
                "'widget_contents' key present")
        t.check(data.get('exit') == 'OK',
                f"exit is 'OK' (got '{data.get('exit')}')")

        wc = data.get('widget_contents', {})
        t.check('sourceviewDialog' in wc,
                f"Window 'sourceviewDialog' in output (keys: {list(wc.keys())})")

        if 'sourceviewDialog' in wc:
            t.check('srcEditor' in wc['sourceviewDialog'],
                    f"'srcEditor' variable in output")
else:
    t.check(False, "OK button not found")
    proc.kill()

t.summary()

#!/usr/bin/env python3
"""
Automated test for examples/standard/terminal using AT-SPI.

Verifies:
1. Window appears with a terminal widget and shortcut buttons
2. Clicking a shortcut button inserts and executes a command
3. The terminal shows the expected command output
4. Clicking Cancel produces valid JSON output
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


def find_button_by_label(window, label_text):
    """Find a button by its label text."""
    for btn in find_widgets(window, Atspi.Role.PUSH_BUTTON):
        name = (btn.get_name() or '')
        if label_text.lower() in name.lower():
            return btn
    return None


def click_button(button):
    """Click a button via AT-SPI action interface."""
    ai = button.get_action_iface()
    if ai:
        ai.do_action(0)
        return True
    return False


def get_terminal_text(window):
    """Get the text content of the terminal widget."""
    terminals = find_widgets(window, Atspi.Role.TERMINAL)
    if not terminals:
        return None
    ti = terminals[0].get_text_iface()
    if ti:
        return Atspi.Text.get_text(ti, 0, -1)
    return None


t = TestRunner()

# Launch the example
t.log("Launching terminal example...")
proc = subprocess.Popen(
    ['./examples/standard/terminal'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(2)

# Get gtkdialog3 PID
our_pid = get_child_pid(proc.pid)
if our_pid is None:
    t.abort("Could not find gtkdialog3 child process")

t.log(f"gtkdialog3 PID: {our_pid}")

# --- Test 1: Window and widgets appear ---
t.begin("testWindowAppears")
window = wait_for_window(our_pid, 'Build Terminal')
t.screenshot('Build Terminal')
if not t.check(window is not None, "Build Terminal window found"):
    proc.kill()
    t.summary()

# Check for terminal widget
terminals = find_widgets(window, Atspi.Role.TERMINAL)
t.check(len(terminals) == 1, f"Terminal widget found (got {len(terminals)})")

# Check for shortcut buttons
btn_make = find_button_by_label(window, 'make -j10')
btn_install = find_button_by_label(window, 'sudo make install')
btn_git = find_button_by_label(window, 'git status')
btn_pwd = find_button_by_label(window, 'pwd')
btn_cancel = find_button_by_label(window, 'Cancel')

t.check(btn_make is not None, "'make -j10' button found")
t.check(btn_install is not None, "'sudo make install' button found")
t.check(btn_git is not None, "'git status' button found")
t.check(btn_pwd is not None, "'pwd' button found")
t.check(btn_cancel is not None, "'Cancel' button found")

# --- Test 2: Click 'pwd' and verify terminal output ---
t.begin("testPwdButton")
if btn_pwd:
    click_button(btn_pwd)
    time.sleep(2)

    text = get_terminal_text(window)
    t.check(text is not None, "Terminal text is readable")
    if text:
        t.check('pwd' in text,
                "'pwd' command appears in terminal")
        # The terminal runs from the project root, so / must appear in output
        t.check('/' in text,
                "Terminal shows a directory path from pwd")

# --- Test 4: Click Cancel and verify JSON output ---
t.begin("testCancelJsonOutput")
if btn_cancel:
    click_button(btn_cancel)
    time.sleep(1)

    retcode = proc.poll()
    if not t.check(retcode is not None,
                   f"Dialog closed after Cancel (exit code {retcode})"
                   if retcode is not None
                   else "Dialog should have closed after Cancel"):
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
        t.check(data.get('exit') == 'Cancel',
                f"exit is 'Cancel' (got '{data.get('exit')}')")

        wc = data.get('widget_contents', {})
        t.check('terminalDialog' in wc,
                f"Window 'terminalDialog' in output (keys: {list(wc.keys())})")
else:
    t.check(False, "Cancel button not found")
    proc.kill()

t.summary()

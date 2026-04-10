#!/usr/bin/env python3
"""
Automated test for examples/standard/webview using AT-SPI.

Verifies:
1. Window appears with the expected title
2. Navigation buttons (Home, LWN.net, Phoronix) and OK button are present
3. Clicking LWN.net navigates the webview
4. Clicking OK produces valid JSON output with the URL
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
    """Find a button by its label text (exact match)."""
    for btn in find_widgets(window, Atspi.Role.PUSH_BUTTON):
        if (btn.get_name() or '').lower() == label_text.lower():
            return btn
    return None


t = TestRunner()

# Launch the example
t.log("Launching webview example...")
proc = subprocess.Popen(
    ['./examples/standard/webview'],
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

# --- Test 1: Window and buttons appear ---
t.begin("testWindowAppears")
window = wait_for_window(our_pid, 'Linux News')
if not t.check(window is not None, "Linux News window found"):
    proc.kill()
    t.summary()

btn_home = find_button_by_label(window, 'Home')
btn_lwn = find_button_by_label(window, 'LWN.net')
btn_phoronix = find_button_by_label(window, 'Phoronix')
btn_ok = find_button_by_label(window, 'OK')

t.check(btn_home is not None, "'Home' button found")
t.check(btn_lwn is not None, "'LWN.net' button found")
t.check(btn_phoronix is not None, "'Phoronix' button found")
t.check(btn_ok is not None, "'OK' button found")

# --- Test 2: Click LWN.net then OK, verify JSON output ---
t.begin("testNavigateAndOutput")
if btn_lwn:
    btn_lwn.get_action_iface().do_action(0)
    time.sleep(3)

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
        t.check('webviewDialog' in wc,
                f"Window 'webviewDialog' in output (keys: {list(wc.keys())})")

        if 'webviewDialog' in wc:
            wd = wc['webviewDialog']
            t.check('webPage' in wd,
                    f"'webPage' variable in output (keys: {list(wd.keys())})")
            url = wd.get('webPage', '')
            t.check('lwn.net' in url,
                    f"webPage URL contains 'lwn.net' (got '{url}')")
else:
    t.check(False, "OK button not found")
    proc.kill()

t.summary()

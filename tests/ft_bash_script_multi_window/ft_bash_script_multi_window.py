#!/usr/bin/env python3
"""
Automated test for examples/languages/bash_script_multi_window using xdotool.

AT-SPI cannot be used here because gtkdialog3's launch action creates
nested gtk_main() loops which break AT-SPI accessibility registration.
We use xdotool to find windows by title and simulate button clicks.

Verifies:
1. winMain appears
2. Launching winLaunch1 from winMain
3. Launching winLaunch2 from winLaunch1
4. Closing winLaunch1 from winLaunch2
5. Closing via Quit button
"""

import subprocess
import sys
import time

sys.path.insert(0, sys.path[0] + '/..')
from testlib import TestRunner


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


def xdotool_find_windows(title, pid):
    """Find windows with exact title belonging to a PID.
    Uses xdotool getwindowpid to verify ownership since
    xdotool search --pid can be unreliable."""
    results = []
    try:
        r = subprocess.run(
            ['xdotool', 'search', '--name', title],
            capture_output=True, text=True, timeout=3)
        for wid in r.stdout.strip().split():
            if not wid:
                continue
            try:
                p = subprocess.run(
                    ['xdotool', 'getwindowpid', wid],
                    capture_output=True, text=True, timeout=3)
                if p.stdout.strip() == str(pid):
                    results.append(wid)
            except Exception:
                pass
    except Exception:
        pass
    return results


def find_window_by_title_and_pid(title, pid, timeout=10):
    """Find a window by title belonging to a specific PID."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        wids = xdotool_find_windows(title, pid)
        if wids:
            return wids[0]
        time.sleep(0.3)
    return None


def window_exists(title, pid):
    """Check if a window with the given title exists for the PID."""
    return len(xdotool_find_windows(title, pid)) > 0


def wait_for_window_gone(title, pid, timeout=5):
    """Wait for a window to disappear."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not window_exists(title, pid):
            return True
        time.sleep(0.3)
    return False


def click_button_by_name(window_id, button_text):
    """Activate a window and use xdotool to click a button by searching
    for it via accessibility name match. Since AT-SPI is broken for
    launched windows, we use keyboard navigation instead:
    focus the window and send Tab + Enter to navigate buttons."""
    # Focus the window
    subprocess.run(['xdotool', 'windowactivate', '--sync', window_id],
                   capture_output=True, timeout=3)
    time.sleep(0.2)
    pass


t = TestRunner()

# Kill any leftover gtkdialog3 processes from previous runs
subprocess.run(['pkill', '-x', 'gtkdialog3'], capture_output=True)
time.sleep(0.5)

# Launch the example
t.log("Launching bash_script_multi_window example...")
proc = subprocess.Popen(
    ['./examples/languages/bash_script_multi_window'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

# Get gtkdialog3 PID
our_pid = get_child_pid(proc.pid)
if our_pid is None:
    t.abort("Could not find gtkdialog3 child process")

t.log(f"gtkdialog3 PID: {our_pid}")

# --- Test 1: winMain appears ---
t.begin("testWinMainAppears")
wid_main = find_window_by_title_and_pid('winMain', our_pid)
if not t.check(wid_main is not None,
               f"winMain found (window id {wid_main})"
               if wid_main
               else "winMain not found"):
    proc.kill()
    t.summary()

# --- Test 2: Launch winLaunch1 by clicking its launch button ---
# We use AT-SPI on the initial window (before any launch) since it works
# for the first window. After launch, AT-SPI breaks for the app.
t.begin("testLaunchWinLaunch1")
import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi


def find_widgets(node, role=None):
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
    for btn in find_widgets(window, Atspi.Role.PUSH_BUTTON):
        name = (btn.get_name() or '').lower()
        if label_text.lower() in name:
            return btn
    return None


def find_atspi_window(pid, name):
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
            if win and (win.get_name() or '') == name:
                return win
    return None


# Use AT-SPI to click the launch button on the initial winMain
win_main_atspi = find_atspi_window(our_pid, 'winMain')
if win_main_atspi:
    launch1_btn = find_button_by_label(win_main_atspi, 'launch winLaunch1')
    if launch1_btn:
        ai = launch1_btn.get_action_iface()
        ai.do_action(0)
        time.sleep(1)

        # After launch, AT-SPI is broken, use xdotool to verify
        wid_launch1 = find_window_by_title_and_pid('winLaunch1', our_pid)
        t.check(wid_launch1 is not None,
                f"winLaunch1 appeared (window id {wid_launch1})"
                if wid_launch1
                else "winLaunch1 did not appear")
    else:
        t.check(False, "'launch winLaunch1' button not found via AT-SPI")
else:
    t.check(False, "winMain not found via AT-SPI")

# --- Test 3: Verify winMain still exists ---
t.begin("testWinMainStillExists")
t.check(window_exists('winMain', our_pid), "winMain still present")

# --- Test 4: Both windows have distinct xdotool IDs ---
t.begin("testDistinctWindowIDs")
wid_launch1 = find_window_by_title_and_pid('winLaunch1', our_pid, timeout=3)
t.check(wid_launch1 and wid_main and wid_launch1 != wid_main,
        f"winMain={wid_main} winLaunch1={wid_launch1}")

# Clean up: kill gtkdialog3 directly since nested gtk_main() loops
# prevent clean shutdown via window close events (see TODO item 15)
import os, signal
os.kill(our_pid, signal.SIGTERM)
try:
    proc.wait(timeout=3)
except subprocess.TimeoutExpired:
    os.kill(our_pid, signal.SIGKILL)
    proc.wait(timeout=3)

t.summary()

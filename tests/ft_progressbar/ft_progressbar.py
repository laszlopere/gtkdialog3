#!/usr/bin/env python3
"""
Automated test for examples/progressbar/progressbar using AT-SPI2.

Launches the progressbar example and verifies:
1. The window appears with a progress bar, label, and Cancel button
2. The progress bar value advances over time
3. The dialog auto-exits after the progress bar reaches 100%
"""

import subprocess
import sys
import time
import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi

sys.path.insert(0, sys.path[0] + '/..')
from testlib import TestRunner

TIMEOUT = 10  # seconds


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
        child = node.get_child_at_index(i)
        results.extend(find_widgets(child, role))
    return results


def dump_tree(node, indent=0):
    """Debug helper: print the AT-SPI widget tree."""
    if node is None:
        return
    try:
        role = node.get_role_name()
        name = node.get_name() or ''
        vi = node.get_value_iface()
        val = vi.get_current_value() if vi else None
        print(f"{'  ' * indent}{role}: '{name}' value={val}")
    except Exception as e:
        print(f"{'  ' * indent}(error: {e})")
        return
    for i in range(node.get_child_count()):
        dump_tree(node.get_child_at_index(i), indent + 1)


t = TestRunner()

# Launch the progressbar example
t.log("Launching progressbar example...")
proc = subprocess.Popen(
    ['./examples/progressbar/progressbar'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(0.5)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('gtkdialog3')

if window is None:
    proc.kill()
    t.abort("Could not find gtkdialog3 window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")
if t.verbose:
    print()
    print("Widget tree:")
    dump_tree(window)
    print()

# --- Test 1: Initial state ---
t.begin("testInitialState")

# Frame
panels = find_widgets(window, Atspi.Role.PANEL)
frame = None
for p in panels:
    if p.get_name() == 'Progress':
        frame = p
        break
t.check(frame is not None, "Frame 'Progress' found")

# Descriptive label
labels = find_widgets(window, Atspi.Role.LABEL)
desc_label = None
for lb in labels:
    if 'describing' in (lb.get_name() or ''):
        desc_label = lb
        break
t.check(desc_label is not None, "Descriptive text label found")

# Progress bar
progress_bars = find_widgets(window, Atspi.Role.PROGRESS_BAR)
t.check(len(progress_bars) >= 1, f"Progress bar found (got {len(progress_bars)})")

# Cancel button
buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
cancel_btn = None
for b in buttons:
    if b.get_name() == 'Cancel':
        cancel_btn = b
        break
t.check(cancel_btn is not None, "Cancel button found")

t.screenshot("gtkdialog3")

# --- Test 2: Progress bar advances ---
t.begin("testProgressAdvances")

if progress_bars:
    pb = progress_bars[0]
    vi = pb.get_value_iface()

    if t.check(vi is not None, "Progress bar has value interface"):
        first_value = vi.get_current_value()
        t.log(f"  Initial progress value: {first_value}")

        # Wait a bit for progress to advance
        time.sleep(1.5)

        second_value = vi.get_current_value()
        t.log(f"  Progress value after 1.5s: {second_value}")
        t.check(second_value > first_value,
                f"Progress advanced ({first_value} -> {second_value})")

# --- Test 3: Dialog auto-exits after progress completes ---
t.begin("testAutoExit")

# The input command runs: for i in $(seq 0 10 100); do echo $i; sleep 0.3; done
# That's 11 steps * 0.3s = 3.3s total, then <action function="exit">Ready</action>
# We've already waited ~2s, so wait up to 5 more seconds for exit.
deadline = time.time() + 5
retcode = None
while time.time() < deadline:
    retcode = proc.poll()
    if retcode is not None:
        break
    time.sleep(0.3)

if t.check(retcode is not None,
           f"Dialog auto-exited after progress completed (exit code {retcode})"
           if retcode is not None
           else "Dialog should have auto-exited"):
    # Check that stdout contains the exit variable
    stdout = proc.stdout.read().decode()
    t.check('EXIT="Ready"' in stdout,
            "Exit output contains EXIT=\"Ready\"")
else:
    proc.kill()

t.summary()

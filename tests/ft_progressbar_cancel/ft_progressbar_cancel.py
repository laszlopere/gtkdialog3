#!/usr/bin/env python3
"""
Automated test for examples/progressbar/progressbar_cancel using AT-SPI2.

Launches the progressbar_cancel example (which has a slow ~21s input
command) and verifies:
1. The window appears with a progress bar and Cancel button
2. The progress bar is advancing
3. Clicking Cancel closes the dialog promptly
4. No orphaned child processes (shell, sleep) remain after exit
"""

import os
import subprocess
import sys
import time
import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi

sys.path.insert(0, sys.path[0] + '/..')
from testlib import TestRunner, launch, wait_for_window, unique_app_name

TIMEOUT = 10  # seconds


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


def do_action(widget, action_name=''):
    """Invoke an action on a widget (e.g. 'click')."""
    ai = widget.get_action_iface()
    if ai is None:
        return False
    for i in range(ai.get_n_actions()):
        if action_name == '' or ai.get_action_name(i) == action_name:
            ai.do_action(i)
            return True
    return False


def get_child_pids(pid):
    """Get all descendant PIDs of a process."""
    try:
        result = subprocess.run(
            ['pgrep', '-P', str(pid)],
            capture_output=True, text=True
        )
        return [int(p) for p in result.stdout.strip().split() if p]
    except Exception:
        return []


def get_all_descendants(pid):
    """Get all descendant PIDs recursively."""
    descendants = []
    children = get_child_pids(pid)
    for child in children:
        descendants.append(child)
        descendants.extend(get_all_descendants(child))
    return descendants


def pid_alive(pid):
    """Check if a process is still alive."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


t = TestRunner()

# Launch the progressbar_cancel example
t.log("Launching progressbar_cancel example...")
APP_NAME = unique_app_name()
proc = launch(['./examples/progressbar/progressbar_cancel'], APP_NAME)

time.sleep(2)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window(APP_NAME, 'Progressbar Cancel')

if window is None:
    proc.kill()
    t.abort("Could not find Progressbar Cancel window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")
if t.verbose:
    print()
    print("Widget tree:")
    dump_tree(window)
    print()

# --- Test 1: Initial state ---
t.begin("testInitialState")

progress_bars = find_widgets(window, Atspi.Role.PROGRESS_BAR)
t.check(len(progress_bars) >= 1, f"Progress bar found (got {len(progress_bars)})")

buttons = find_widgets(window, Atspi.Role.PUSH_BUTTON)
cancel_btn = None
for b in buttons:
    if b.get_name() == 'Cancel':
        cancel_btn = b
        break
t.check(cancel_btn is not None, "Cancel button found")

# --- Test 2: Progress bar is advancing ---
t.begin("testProgressAdvances")

if progress_bars:
    pb = progress_bars[0]
    vi = pb.get_value_iface()
    if t.check(vi is not None, "Progress bar has value interface"):
        first_value = vi.get_current_value()
        time.sleep(1.5)
        second_value = vi.get_current_value()
        t.log(f"  Progress: {first_value} -> {second_value}")
        t.check(second_value > first_value,
                f"Progress advanced ({first_value} -> {second_value})")
        t.check(second_value < 1.0,
                f"Progress not yet complete ({second_value} < 1.0)")

# --- Test 3: Record child processes, then Cancel ---
t.begin("testCancelKillsChildren")

# Record all descendant PIDs of the wrapper shell before cancelling
descendants = get_all_descendants(proc.pid)
t.log(f"  Descendant PIDs before cancel: {descendants}")
t.check(len(descendants) >= 1,
        f"Child processes exist before cancel (got {len(descendants)})")

t.screenshot("Progressbar Cancel")

# Click Cancel
if cancel_btn:
    do_action(cancel_btn, 'click')

# Wait for dialog to close
deadline = time.time() + 5
retcode = None
while time.time() < deadline:
    retcode = proc.poll()
    if retcode is not None:
        break
    time.sleep(0.2)

if not t.check(retcode is not None,
               f"Dialog closed after Cancel (exit code {retcode})"
               if retcode is not None
               else "Dialog should have closed after Cancel"):
    proc.kill()
    proc.wait()

# Give child processes a moment to be cleaned up
time.sleep(0.5)

# Check that all descendant processes are gone
orphans = [pid for pid in descendants if pid_alive(pid)]
t.log(f"  Orphaned PIDs after cancel: {orphans}")
if orphans:
    # Log details about orphans for debugging
    for pid in orphans:
        try:
            result = subprocess.run(
                ['ps', '-p', str(pid), '-o', 'pid,ppid,cmd'],
                capture_output=True, text=True
            )
            t.log(f"  Orphan details: {result.stdout.strip()}")
        except Exception:
            pass
    # Clean up orphans so they don't linger
    for pid in orphans:
        try:
            os.kill(pid, 9)
        except OSError:
            pass
t.check(len(orphans) == 0,
        f"No orphaned child processes remain (found {len(orphans)})")

t.summary()

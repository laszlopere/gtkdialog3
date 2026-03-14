#!/usr/bin/env python3
"""
Automated test for examples/languages/bash_script_multi_window using AT-SPI2.

This example has 3 windows (winMain, winLaunch1, winLaunch2) that can
launch and close each other. Only winMain is shown initially.

Verifies:
1. winMain appears with expected buttons
2. Launching winLaunch1 from winMain
3. Launching winLaunch2 from winLaunch1
4. Closing winLaunch1 from winLaunch2
5. Closing via Quit button
"""

import subprocess
import sys
import time
import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi

TIMEOUT = 10


def wait_for_window(name, timeout=TIMEOUT):
    """Wait for a window matching the title to appear in AT-SPI tree."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        desktop = Atspi.get_desktop(0)
        for i in range(desktop.get_child_count()):
            app = desktop.get_child_at_index(i)
            if app is None:
                continue
            for j in range(app.get_child_count()):
                win = app.get_child_at_index(j)
                if win and (win.get_name() or '') == name:
                    return win
        time.sleep(0.3)
    return None


def wait_for_window_gone(name, timeout=TIMEOUT):
    """Wait for a window to disappear from AT-SPI tree."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        found = False
        desktop = Atspi.get_desktop(0)
        for i in range(desktop.get_child_count()):
            app = desktop.get_child_at_index(i)
            if app is None:
                continue
            for j in range(app.get_child_count()):
                win = app.get_child_at_index(j)
                if win and (win.get_name() or '') == name:
                    found = True
                    break
            if found:
                break
        if not found:
            return True
        time.sleep(0.3)
    return False


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
    """Find a button whose label contains the given text."""
    for btn in find_widgets(window, Atspi.Role.PUSH_BUTTON):
        name = (btn.get_name() or '').lower()
        if label_text.lower() in name:
            return btn
    return None


def do_action(widget, action_name='click'):
    """Invoke an action on a widget."""
    ai = widget.get_action_iface()
    if ai is None:
        return False
    for i in range(ai.get_n_actions()):
        if action_name == '' or ai.get_action_name(i) == action_name:
            ai.do_action(i)
            return True
    return False


def test_pass(msg):
    print(f"  PASS: {msg}")


def test_fail(msg):
    print(f"  FAIL: {msg}")
    global failures
    failures += 1


failures = 0

# Launch the example
print("Launching bash_script_multi_window example...")
proc = subprocess.Popen(
    ['./examples/languages/bash_script_multi_window'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

# --- Test 1: winMain appears ---
print("\nTest 1: winMain appears")
win_main = wait_for_window('winMain')
if win_main:
    test_pass("winMain found")
else:
    test_fail("winMain not found")
    proc.kill()
    sys.exit(1)

# Check buttons exist
launch1_btn = find_button_by_label(win_main, 'launch winLaunch1')
launch2_btn = find_button_by_label(win_main, 'launch winLaunch2')
quit_btn = find_button_by_label(win_main, 'quit')

if launch1_btn:
    test_pass("'launch winLaunch1' button found in winMain")
else:
    test_fail("'launch winLaunch1' button not found in winMain")

if launch2_btn:
    test_pass("'launch winLaunch2' button found in winMain")
else:
    test_fail("'launch winLaunch2' button not found in winMain")

# --- Test 2: Launch winLaunch1 from winMain ---
print("\nTest 2: Launch winLaunch1 from winMain")
if launch1_btn:
    do_action(launch1_btn)
    time.sleep(0.5)
    win_launch1 = wait_for_window('winLaunch1')
    if win_launch1:
        test_pass("winLaunch1 appeared")
    else:
        test_fail("winLaunch1 did not appear")

# --- Test 3: Launch winLaunch2 from winLaunch1 ---
print("\nTest 3: Launch winLaunch2 from winLaunch1")
if win_launch1:
    launch2_from_1 = find_button_by_label(win_launch1, 'launch winLaunch2')
    if launch2_from_1:
        do_action(launch2_from_1)
        time.sleep(0.5)
        win_launch2 = wait_for_window('winLaunch2')
        if win_launch2:
            test_pass("winLaunch2 appeared")
        else:
            test_fail("winLaunch2 did not appear")
    else:
        test_fail("'launch winLaunch2' button not found in winLaunch1")

# --- Test 4: Close winLaunch1 from winLaunch2 ---
print("\nTest 4: Close winLaunch1 from winLaunch2")
if win_launch2:
    close1_from_2 = find_button_by_label(win_launch2, 'closewindow winLaunch1')
    if close1_from_2:
        do_action(close1_from_2)
        time.sleep(0.5)
        if wait_for_window_gone('winLaunch1', timeout=3):
            test_pass("winLaunch1 closed")
        else:
            test_fail("winLaunch1 should have closed")
    else:
        test_fail("'closewindow winLaunch1' button not found in winLaunch2")

# --- Test 5: Close via Quit on winMain ---
print("\nTest 5: Close via Quit on winMain")
# Re-find winMain in case AT-SPI references went stale
win_main = wait_for_window('winMain', timeout=3)
if win_main:
    quit_btn = find_button_by_label(win_main, 'quit')
    if quit_btn:
        do_action(quit_btn)
        time.sleep(1)
        retcode = proc.poll()
        if retcode is not None:
            test_pass(f"Application closed via Quit (exit code {retcode})")
        else:
            test_fail("Application should have closed after Quit")
            proc.kill()
    else:
        test_fail("Quit button not found in winMain")
        proc.kill()
else:
    test_fail("winMain not found for Quit test")
    proc.kill()

# Print summary
print(f"\n{'=' * 40}")
if failures == 0:
    print("All tests PASSED")
    sys.exit(0)
else:
    print(f"{failures} test(s) FAILED")
    sys.exit(1)

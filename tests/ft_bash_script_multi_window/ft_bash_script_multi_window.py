#!/usr/bin/env python3
"""
Automated test for examples/languages/bash_script_multi_window using AT-SPI.

Verifies:
1. winMain appears
2. Launching winLaunch1 from winMain
3. Launching winLaunch2 from winLaunch1
4. Closing winLaunch1 via closewindow button, then re-launching it
5. Closing winLaunch2 via window manager close event, then re-launching it
6. Closing via Quit button
"""

import ctypes
import ctypes.util
import struct
import subprocess
import sys
import time

import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi

sys.path.insert(0, sys.path[0] + '/..')
from testlib import TestRunner

TIMEOUT = 10  # seconds


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
                try:
                    win.get_name()
                    windows.append(win)
                except Exception:
                    pass
    return windows


def window_names(pid):
    """Return sorted list of window names for a PID."""
    return sorted(w.get_name() for w in find_app_windows(pid))


def wait_for_window(pid, name, timeout=TIMEOUT):
    """Wait for an AT-SPI window with the given name to appear."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for win in find_app_windows(pid):
            if (win.get_name() or '') == name:
                return win
        time.sleep(0.3)
    return None


def wait_for_window_gone(pid, name, timeout=5):
    """Wait for a window to disappear from AT-SPI."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if name not in window_names(pid):
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
    """Find a button by its label text (case-insensitive substring match)."""
    for btn in find_widgets(window, Atspi.Role.PUSH_BUTTON):
        name = (btn.get_name() or '').lower()
        if label_text.lower() in name:
            return btn
    return None


def click_button(button):
    """Click a button via AT-SPI action interface."""
    ai = button.get_action_iface()
    if ai:
        ai.do_action(0)
        return True
    return False


def xdotool_find_window(title, pid):
    """Find an X window by title belonging to a specific PID."""
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
                    return int(wid)
            except Exception:
                pass
    except Exception:
        pass
    return None


def wm_close_window(title, pid):
    """Close a window by sending a WM_DELETE_WINDOW X11 client message.
    This mimics the window manager's close button, triggering GTK's
    delete-event signal (unlike xdotool windowclose which destroys
    the X window directly)."""
    xwid = xdotool_find_window(title, pid)
    if xwid is None:
        return False

    libX11 = ctypes.cdll.LoadLibrary(ctypes.util.find_library('X11'))
    libX11.XOpenDisplay.restype = ctypes.c_void_p
    libX11.XInternAtom.restype = ctypes.c_ulong

    dpy = libX11.XOpenDisplay(None)
    if not dpy:
        return False

    wm_protocols = libX11.XInternAtom(dpy, b'WM_PROTOCOLS', False)
    wm_delete = libX11.XInternAtom(dpy, b'WM_DELETE_WINDOW', False)

    # Build XClientMessageEvent (192-byte XEvent union, x86_64 layout)
    event = bytearray(192)
    struct.pack_into('i', event, 0, 33)             # type = ClientMessage
    struct.pack_into('Q', event, 8, 0)              # serial
    struct.pack_into('i', event, 16, 1)             # send_event = True
    struct.pack_into('Q', event, 24, dpy)           # display
    struct.pack_into('Q', event, 32, xwid)          # window
    struct.pack_into('Q', event, 40, wm_protocols)  # message_type
    struct.pack_into('i', event, 48, 32)            # format = 32
    struct.pack_into('q', event, 56, wm_delete)     # data.l[0]

    libX11.XSendEvent(dpy, xwid, False, 0, bytes(event))
    libX11.XFlush(dpy)
    libX11.XCloseDisplay(dpy)
    return True


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
win_main = wait_for_window(our_pid, 'winMain')
if not t.check(win_main is not None, "winMain found via AT-SPI"):
    proc.kill()
    t.summary()

# --- Test 2: Launch winLaunch1 from winMain ---
t.begin("testLaunchWinLaunch1")
btn = find_button_by_label(win_main, 'launch winLaunch1')
t.check(btn is not None, "'launch winLaunch1' button found")
if btn:
    click_button(btn)
    time.sleep(1)
win_launch1 = wait_for_window(our_pid, 'winLaunch1', timeout=5)
t.check(win_launch1 is not None, "winLaunch1 appeared")

# --- Test 3: Launch winLaunch2 from winLaunch1 ---
t.begin("testLaunchWinLaunch2")
if win_launch1:
    btn = find_button_by_label(win_launch1, 'launch winLaunch2')
    t.check(btn is not None, "'launch winLaunch2' button found on winLaunch1")
    if btn:
        click_button(btn)
        time.sleep(1)
    win_launch2 = wait_for_window(our_pid, 'winLaunch2', timeout=5)
    t.check(win_launch2 is not None, "winLaunch2 appeared")
else:
    t.check(False, "Skipped: winLaunch1 not available")
    win_launch2 = None

t.check(window_names(our_pid) == ['winLaunch1', 'winLaunch2', 'winMain'],
        f"All three windows present: {window_names(our_pid)}")

# --- Test 4: Close winLaunch1 via closewindow button, then re-launch ---
t.begin("testCloseAndRelaunchViaButton")
if win_launch2:
    btn = find_button_by_label(win_launch2, 'closewindow winLaunch1')
    t.check(btn is not None,
            "'closewindow winLaunch1' button found on winLaunch2")
    if btn:
        click_button(btn)
        time.sleep(1)
    t.check(wait_for_window_gone(our_pid, 'winLaunch1'),
            "winLaunch1 closed via button")
    t.check(window_names(our_pid) == ['winLaunch2', 'winMain'],
            f"winMain and winLaunch2 remain: {window_names(our_pid)}")

    # Re-launch winLaunch1 from winMain
    win_main = wait_for_window(our_pid, 'winMain', timeout=3)
    btn = find_button_by_label(win_main, 'launch winLaunch1')
    if btn:
        click_button(btn)
        time.sleep(1)
    win_launch1 = wait_for_window(our_pid, 'winLaunch1', timeout=5)
    t.check(win_launch1 is not None, "winLaunch1 re-launched after close")
    t.check(window_names(our_pid) == ['winLaunch1', 'winLaunch2', 'winMain'],
            f"All three windows present again: {window_names(our_pid)}")
else:
    t.check(False, "Skipped: winLaunch2 not available")

# --- Test 5: Close winLaunch2 via WM close event, then re-launch ---
t.begin("testCloseAndRelaunchViaWM")
closed = wm_close_window('winLaunch2', our_pid)
t.check(closed, "Sent WM_DELETE_WINDOW to winLaunch2")
t.check(wait_for_window_gone(our_pid, 'winLaunch2'),
        "winLaunch2 closed via WM event")
t.check(window_names(our_pid) == ['winLaunch1', 'winMain'],
        f"winMain and winLaunch1 remain: {window_names(our_pid)}")

# Re-launch winLaunch2 from winLaunch1
win_launch1 = wait_for_window(our_pid, 'winLaunch1', timeout=3)
if win_launch1:
    btn = find_button_by_label(win_launch1, 'launch winLaunch2')
    if btn:
        click_button(btn)
        time.sleep(1)
    win_launch2 = wait_for_window(our_pid, 'winLaunch2', timeout=5)
    t.check(win_launch2 is not None, "winLaunch2 re-launched after WM close")
    t.check(window_names(our_pid) == ['winLaunch1', 'winLaunch2', 'winMain'],
            f"All three windows present again: {window_names(our_pid)}")
else:
    t.check(False, "Skipped: winLaunch1 not available")

# --- Test 6: Quit from winMain ---
t.begin("testQuitFromMain")
win_main = wait_for_window(our_pid, 'winMain', timeout=3)
if win_main:
    quit_btn = find_button_by_label(win_main, 'Quit')
    t.check(quit_btn is not None, "'Quit' button found on winMain")
    if quit_btn:
        click_button(quit_btn)
        try:
            proc.wait(timeout=5)
            t.check(True, f"Process exited (code {proc.returncode})")
        except subprocess.TimeoutExpired:
            t.check(False, "Process did not exit after Quit")
            proc.kill()
            proc.wait(timeout=3)
else:
    t.check(False, "winMain not found for quit test")
    proc.kill()
    proc.wait(timeout=3)

t.summary()

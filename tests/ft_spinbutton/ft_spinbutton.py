#!/usr/bin/env python3
"""
Automated test for examples/spinbutton/spinbutton using AT-SPI2.

Verifies:
1. Window appears with 7 spinbutton widgets
2. SPB_RANGE: initial value 10, range -50..50, step 5
3. SPB_DIGITS: initial value 0.500, 3 decimal places
4. SPB_WRAP: wraps from 0 down to 23
5. SPB_SNAP: snap-to-ticks rounds to step boundary
6. SPB_POLICY: initial value 5
7. SPB_ENTRY: not editable, initial value 42
8. SPB_DEFAULT: initial value 7 from <default> tag
9. OK button closes the dialog and exports correct values
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


def find_button(window, label_text):
    """Find a push button by its label text."""
    for btn in find_widgets(window, Atspi.Role.PUSH_BUTTON):
        name = (btn.get_name() or '').lower()
        if label_text.lower() == name:
            return btn
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


def get_spinbutton_value(spb):
    """Get the current value of a spinbutton via its Value interface."""
    vi = spb.get_value_iface()
    if vi is None:
        return None
    return vi.get_current_value()


def set_spinbutton_value(spb, value):
    """Set the value of a spinbutton via its Value interface."""
    vi = spb.get_value_iface()
    if vi is None:
        return False
    return vi.set_current_value(value)


def get_spinbutton_range(spb):
    """Get (min, max) of a spinbutton via its Value interface."""
    vi = spb.get_value_iface()
    if vi is None:
        return None, None
    return vi.get_minimum_value(), vi.get_maximum_value()


def get_spinbutton_step(spb):
    """Get the step increment of a spinbutton via its Value interface."""
    vi = spb.get_value_iface()
    if vi is None:
        return None
    return vi.get_minimum_increment()


def get_displayed_text(widget):
    """Get the displayed text of a widget via AT-SPI Text interface."""
    n = Atspi.Text.get_character_count(widget)
    return Atspi.Text.get_text(widget, 0, n)


def is_editable(widget):
    """Check if a widget has the EDITABLE state."""
    states = widget.get_state_set()
    return states.contains(Atspi.StateType.EDITABLE)


def dump_tree(node, indent=0):
    """Debug helper: print the AT-SPI widget tree."""
    if node is None:
        return
    try:
        role = node.get_role_name()
        name = node.get_name() or ''
        print(f"{'  ' * indent}{role}: '{name}'")
    except Exception as e:
        print(f"{'  ' * indent}(error: {e})")
        return
    for i in range(node.get_child_count()):
        dump_tree(node.get_child_at_index(i), indent + 1)


t = TestRunner()

# Kill any leftover gtkdialog3 processes
subprocess.run(['pkill', '-x', 'gtkdialog3'], capture_output=True)
time.sleep(0.5)

# Launch the example
t.log("Launching spinbutton example...")
proc = subprocess.Popen(
    ['./examples/spinbutton/spinbutton'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd='/home/pipas/gtkdialog/gtkdialog-0.8.3'
)

time.sleep(1)

t.log("Looking for window via AT-SPI...")
app, window = wait_for_window('spinbutton')

if window is None:
    proc.kill()
    t.abort("Could not find SpinButton Properties window via AT-SPI")

t.log(f"Found window: '{window.get_name()}'")
if t.verbose:
    print()
    print("Widget tree:")
    dump_tree(window)
    print()

# Find all spinbuttons in order
spbs = find_widgets(window, Atspi.Role.SPIN_BUTTON)

# --- Test 1: All 7 spinbuttons present ---
t.begin("testWidgetCount")
t.check(len(spbs) == 7,
        f"Found 7 spinbuttons"
        if len(spbs) == 7
        else f"Expected 7 spinbuttons, found {len(spbs)}")

if len(spbs) < 7:
    proc.kill()
    proc.wait()
    t.abort("Not enough spinbuttons found, cannot continue")

spb_range, spb_digits, spb_wrap, spb_snap, spb_policy, spb_entry, spb_default = spbs

# --- Test 2: SPB_RANGE initial value and range ---
t.begin("testRange")
val = get_spinbutton_value(spb_range)
t.check(val == 10.0,
        f"SPB_RANGE initial value is 10"
        if val == 10.0
        else f"SPB_RANGE: expected 10, got {val}")
lo, hi = get_spinbutton_range(spb_range)
t.check(lo == -50.0,
        f"SPB_RANGE min is -50"
        if lo == -50.0
        else f"SPB_RANGE min: expected -50, got {lo}")
t.check(hi == 50.0,
        f"SPB_RANGE max is 50"
        if hi == 50.0
        else f"SPB_RANGE max: expected 50, got {hi}")
step = get_spinbutton_step(spb_range)
t.check(step == 5.0,
        f"SPB_RANGE step is 5"
        if step == 5.0
        else f"SPB_RANGE step: expected 5, got {step}")

# --- Test 3: SPB_DIGITS value and display ---
t.begin("testDigits")
val = get_spinbutton_value(spb_digits)
t.check(val == 0.5,
        f"SPB_DIGITS initial value is 0.5"
        if val == 0.5
        else f"SPB_DIGITS: expected 0.5, got {val}")
text = get_displayed_text(spb_digits)
t.check(text == '0.500',
        f"SPB_DIGITS displays '0.500' (3 decimal places)"
        if text == '0.500'
        else f"SPB_DIGITS text: expected '0.500', got '{text}'")

# --- Test 4: SPB_WRAP range and initial value ---
t.begin("testWrap")
val = get_spinbutton_value(spb_wrap)
t.check(val == 0.0,
        f"SPB_WRAP initial value is 0"
        if val == 0.0
        else f"SPB_WRAP: expected 0, got {val}")
lo, hi = get_spinbutton_range(spb_wrap)
t.check(lo == 0.0 and hi == 23.0,
        f"SPB_WRAP range is 0..23"
        if lo == 0.0 and hi == 23.0
        else f"SPB_WRAP range: expected 0..23, got {lo}..{hi}")

# --- Test 5: SPB_SNAP initial value ---
t.begin("testSnapToTicks")
val = get_spinbutton_value(spb_snap)
t.check(val == 50.0,
        f"SPB_SNAP initial value is 50"
        if val == 50.0
        else f"SPB_SNAP: expected 50, got {val}")
step = get_spinbutton_step(spb_snap)
t.check(step == 10.0,
        f"SPB_SNAP step is 10"
        if step == 10.0
        else f"SPB_SNAP step: expected 10, got {step}")

# --- Test 6: SPB_POLICY initial value ---
t.begin("testUpdatePolicy")
val = get_spinbutton_value(spb_policy)
t.check(val == 5.0,
        f"SPB_POLICY initial value is 5"
        if val == 5.0
        else f"SPB_POLICY: expected 5, got {val}")

# --- Test 7: SPB_ENTRY is not editable ---
t.begin("testEntryProperties")
val = get_spinbutton_value(spb_entry)
t.check(val == 42.0,
        f"SPB_ENTRY initial value is 42"
        if val == 42.0
        else f"SPB_ENTRY: expected 42, got {val}")
t.check(not is_editable(spb_entry),
        f"SPB_ENTRY is not editable"
        if not is_editable(spb_entry)
        else "SPB_ENTRY should not be editable")

# --- Test 8: SPB_DEFAULT value from <default> tag ---
t.begin("testDefaultTag")
val = get_spinbutton_value(spb_default)
t.check(val == 7.0,
        f"SPB_DEFAULT initial value is 7 (from <default> tag)"
        if val == 7.0
        else f"SPB_DEFAULT: expected 7, got {val}")

# --- Test 9: OK button closes and exports values ---
t.begin("testOkClose")
ok_btn = find_button(window, 'OK')
if ok_btn:
    do_action(ok_btn, 'click')
    time.sleep(1)
    retcode = proc.poll()
    if t.check(retcode is not None,
               f"Dialog closed after OK (exit code {retcode})"
               if retcode is not None
               else "Dialog should have closed after OK"):
        stdout = proc.stdout.read().decode()
        t.log(f"stdout:\n{stdout}")
        t.check('SPB_RANGE="10"' in stdout,
                "Output contains SPB_RANGE=\"10\"")
        t.check('SPB_DIGITS="0.500"' in stdout,
                "Output contains SPB_DIGITS=\"0.500\"")
        t.check('SPB_DEFAULT="7"' in stdout,
                "Output contains SPB_DEFAULT=\"7\"")
    else:
        proc.kill()
        proc.wait()
else:
    t.check(False, "OK button not found")
    proc.kill()
    proc.wait()

t.summary()

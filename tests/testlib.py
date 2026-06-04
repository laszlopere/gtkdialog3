"""Shared test framework for functional tests.

Usage:
    from testlib import TestRunner
    t = TestRunner()
    t.begin("testInitialState")
    t.check(condition, "description")
    t.end()
    t.summary()

Without --verbose, prints a brief one-line-per-step report.
With --verbose, prints detailed PASS/FAIL lines and extra log output.
"""

import os
import subprocess
import sys
import time
import warnings

# Suppress GObject/AT-SPI deprecation warnings that clutter test output
warnings.filterwarnings('ignore', category=DeprecationWarning)

STEP_NAME_WIDTH = 24

# Project root (one level above the tests/ directory holding this file).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def unique_app_name(suffix=''):
    """A per-test, per-process AT-SPI application name.

    gtkdialog instances all share the application name "gtkdialog3", so a
    test that locates its window by scanning the AT-SPI tree can latch onto
    a stale or concurrently-running instance -- the main source of flaky
    failures.  Launching gtkdialog with this unique name (see launch())
    makes every instance individually addressable.

    The name combines the test script's basename with the test process PID,
    so it is stable within a run yet unique across runs and across parallel
    tests.
    """
    base = os.path.basename(sys.argv[0])
    if base.endswith('.py'):
        base = base[:-3]
    name = "%s_%d" % (base, os.getpid())
    return name + suffix if suffix else name


def launch(argv, app_name, cwd=PROJECT_ROOT, **kwargs):
    """Launch a gtkdialog example/binary tagged with a unique app_name.

    The name is passed via the GTKDIALOG_DBUS_NAME environment variable,
    which gtkdialog applies as its AT-SPI application name and default
    window title.  Using the environment (rather than a command line flag)
    means it works even when argv points at a wrapper shell script that
    invokes gtkdialog internally without forwarding its options.

    Returns the subprocess.Popen object.
    """
    env = dict(os.environ)
    env['GTKDIALOG_DBUS_NAME'] = app_name
    kwargs.setdefault('stdout', subprocess.PIPE)
    kwargs.setdefault('stderr', subprocess.PIPE)
    return subprocess.Popen(argv, cwd=cwd, env=env, **kwargs)


def wait_for_window(app_name, title_substring=None, timeout=10):
    """Wait for the window of the gtkdialog instance named app_name.

    Matches the AT-SPI *application* by its exact name (set via launch()),
    which is unique per instance, then returns one of its toplevel windows.
    When title_substring is given (e.g. to pick one window of a multi-window
    dialog) the first window whose name contains it is returned; otherwise
    the first window is returned.

    Returns (application, window), or (None, None) on timeout.
    """
    import gi
    gi.require_version('Atspi', '2.0')
    from gi.repository import Atspi

    deadline = time.time() + timeout
    while time.time() < deadline:
        desktop = Atspi.get_desktop(0)
        for i in range(desktop.get_child_count()):
            app = desktop.get_child_at_index(i)
            if app is None or (app.get_name() or '') != app_name:
                continue
            for j in range(app.get_child_count()):
                win = app.get_child_at_index(j)
                if win is None:
                    continue
                if title_substring is None or \
                        title_substring.lower() in (win.get_name() or '').lower():
                    return app, win
        time.sleep(0.2)
    return None, None


class TestRunner:
    def __init__(self):
        self.verbose = '--verbose' in sys.argv
        self.screenshots = '--screenshot' in sys.argv
        self.test_name = None
        self._steps = []       # list of (name, checks, failures, elapsed)
        self._cur_step = None
        self._cur_checks = 0
        self._cur_failures = 0
        self._cur_start = 0
        self._total_checks = 0
        self._total_failures = 0
        self._aborted = False

        # Derive test name from script path
        script = os.path.basename(sys.argv[0])
        if script.endswith('.py'):
            script = script[:-3]
        self.test_name = script

        # Print the test path header
        script_path = sys.argv[0]
        # Try to make it relative to cwd
        try:
            script_path = os.path.relpath(script_path)
        except ValueError:
            pass
        # Strip .py extension for display
        if script_path.endswith('.py'):
            script_path = script_path[:-3]
        self._script_path = script_path
        if not self.verbose:
            print(script_path)

    def begin(self, step_name):
        """Start a named test step."""
        if self._cur_step is not None:
            self.end()
        self._cur_step = step_name
        self._cur_checks = 0
        self._cur_failures = 0
        self._cur_start = time.time()
        if self.verbose:
            print(f"\n{step_name}")

    def check(self, condition, msg):
        """Record a check. Returns the condition for convenience."""
        self._cur_checks += 1
        self._total_checks += 1
        if condition:
            if self.verbose:
                print(f"  PASS: {msg}")
        else:
            self._cur_failures += 1
            self._total_failures += 1
            if self.verbose:
                print(f"  FAIL: {msg}")
        return condition

    def end(self):
        """End the current test step and print its summary line."""
        if self._cur_step is None:
            return
        elapsed = time.time() - self._cur_start
        elapsed_s = int(elapsed)
        self._steps.append((self._cur_step, self._cur_checks,
                            self._cur_failures, elapsed_s))
        if not self.verbose:
            status = "FAILURE" if self._cur_failures > 0 else "SUCCESS"
            name = self._cur_step.ljust(STEP_NAME_WIDTH)
            print(f"  {name}: {status} ({self._cur_checks:4d} checks, "
                  f"{elapsed_s:3d}s)")
        self._cur_step = None

    def log(self, msg):
        """Print a message only in verbose mode."""
        if self.verbose:
            print(msg)

    def abort(self, msg):
        """Abort the test run with an error message."""
        self._aborted = True
        if self._cur_step is not None:
            self._cur_failures += 1
            self._total_failures += 1
            self.end()
        if self.verbose:
            print(f"\nABORT: {msg}")
        # Print final summary even on abort
        self._print_summary()
        sys.exit(1)

    def summary(self):
        """Print the final summary line and exit."""
        if self._cur_step is not None:
            self.end()
        self._print_summary()
        sys.exit(0 if self._total_failures == 0 else 1)

    def screenshot(self, window_title):
        """Capture a screenshot of the named window if --screenshot is set.

        Uses xdotool to find the window by title and ImageMagick
        import to capture it as PNG.  Screenshots are saved under
        tests/screenshots/<test_name>.png.
        """
        if not self.screenshots or not window_title:
            return
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        tests_dir = os.path.dirname(script_dir)
        shot_dir = os.path.join(tests_dir, 'screenshots')
        os.makedirs(shot_dir, exist_ok=True)
        out_path = os.path.join(shot_dir, self.test_name + '.png')
        try:
            wid = subprocess.check_output(
                ['xdotool', 'search', '--name', window_title],
                stderr=subprocess.DEVNULL
            ).decode().strip().split('\n')[0]
            subprocess.run(
                ['import', '-frame', '-window', wid, out_path],
                check=True, stderr=subprocess.DEVNULL
            )
            if self.verbose:
                print(f"  screenshot: {out_path}")
        except (subprocess.CalledProcessError, IndexError,
                FileNotFoundError):
            if self.verbose:
                print("  screenshot: SKIPPED"
                      " (window not found or tools missing)")

    def _print_summary(self):
        passed = self._total_checks - self._total_failures
        total_time = sum(s[3] for s in self._steps)
        if self._aborted:
            status = "FAILURE"
        elif self._total_failures == 0:
            status = "SUCCESS"
        else:
            status = "FAILURE"
        if self.verbose:
            print(f"\n{'=' * 40}")
            if self._aborted:
                print(f"ABORTED ({self._total_checks} checks completed)")
            elif self._total_failures == 0:
                print(f"All tests PASSED ({self._total_checks} checks)")
            else:
                print(f"{self._total_failures} of {self._total_checks} "
                      f"check(s) FAILED")
        else:
            print(f"{status} (passed {passed} of {self._total_checks}, "
                  f"{total_time}s): {self.test_name}")

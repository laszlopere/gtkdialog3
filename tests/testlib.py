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

import sys
import time
import warnings

# Suppress GObject/AT-SPI deprecation warnings that clutter test output
warnings.filterwarnings('ignore', category=DeprecationWarning)

STEP_NAME_WIDTH = 24


class TestRunner:
    def __init__(self):
        self.verbose = '--verbose' in sys.argv
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
        import os
        script = os.path.basename(sys.argv[0])
        if script.endswith('.py'):
            script = script[:-3]
        self.test_name = script

        # Print the test path header
        import os.path
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

    def _print_summary(self):
        passed = self._total_checks - self._total_failures
        total_time = sum(s[3] for s in self._steps)
        if self._total_failures == 0:
            status = "SUCCESS"
        else:
            status = "FAILURE"
        if self.verbose:
            print(f"\n{'=' * 40}")
            if self._total_failures == 0:
                print(f"All tests PASSED ({self._total_checks} checks)")
            else:
                print(f"{self._total_failures} of {self._total_checks} "
                      f"check(s) FAILED")
        else:
            print(f"{status} (passed {passed} of {self._total_checks}, "
                  f"{total_time}s): {self.test_name}")

#!/bin/bash
# Run all functional tests and print a summary.
# Pass --verbose to forward it to individual tests.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARGS=""
for arg in "$@"; do
    case "$arg" in
        --verbose|--screenshot) ARGS="$ARGS $arg" ;;
    esac
done

total=0
failed=0

for test_dir in "$SCRIPT_DIR"/ft_*; do
    test_name="$(basename "$test_dir")"
    test_script="$test_dir/$test_name.py"
    if [ ! -f "$test_script" ]; then
        continue
    fi
    total=$((total + 1))
    python3 "$test_script" $ARGS
    if [ $? -ne 0 ]; then
        failed=$((failed + 1))
    fi
done

echo ""
if [ "$failed" -eq 0 ]; then
    echo "ALL PASSED ($total tests)"
else
    echo "FAILED $failed of $total tests"
fi

exit "$failed"

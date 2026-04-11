#!/bin/sh

cd "$(dirname "$0")"

gtkdialog3 \
    --ui-file=builder-entries_functions.ui \
    --include=builder-entries_functions.functions \
    --program=login_window

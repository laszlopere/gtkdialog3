#!/bin/sh

cd "$(dirname "$0")"

gtkdialog3 --ui-file=builder-toolbar_buttons.ui \
          --program=MAIN_WINDOW

#!/bin/sh

cd "$(dirname "$0")"

gtkdialog3 --glade-xml=glade-entries_functions.ui \
          --include=glade-entries_functions.functions \
          --program=login_window

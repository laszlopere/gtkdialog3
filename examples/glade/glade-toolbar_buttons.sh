#!/bin/sh

cd "$(dirname "$0")"

gtkdialog3 --glade-xml=glade-toolbar_buttons.ui \
          --program=MAIN_WINDOW

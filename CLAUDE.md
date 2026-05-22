# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GtkDialog3 is a C utility for building GTK3 GUIs declaratively. Users define UIs using an XML-like markup language (embedded in bash scripts or standalone), which is parsed by a Flex/Bison lexer/parser and executed by a VM-like automaton that creates GTK widgets at runtime.

## Build

Autotools-based build system. Requires `gcc`, `flex`, `bison`, `autoconf`, `automake`, `pkg-config`, GTK3 dev libraries, and optionally VTE 2.91 for terminal widget support.

```bash
# From a fresh checkout:
./autogen.sh
make

# If configure already exists:
./configure
make
```

The binary is built at `src/gtkdialog3`.

## Tests

Functional tests use Python 3 with AT-SPI2 (accessibility) to drive the GUI programmatically. Each test lives in `tests/ft_<name>/ft_<name>.py` and uses the shared `tests/testlib.py` framework.

```bash
# Run all functional tests:
./tests/runallfunctionaltests.sh

# Run all with verbose output:
./tests/runallfunctionaltests.sh --verbose

# Run a single test:
python3 tests/ft_checkbox/ft_checkbox.py [--verbose]
```

Tests require a running display server (X11 or Wayland with XWayland) and the AT-SPI2 accessibility bus.

## Architecture

### Parser Pipeline
`gtkdialog_lexer.l` (Flex) -> `gtkdialog_parser.y` (Bison) -> `automaton.c` (widget creation & execution)

The lexer tokenizes the XML-like input, the parser builds an instruction list, and the automaton walks those instructions to create GTK widgets and wire up signal handlers.

### Core Modules
- **automaton.c** - VM executing parsed instructions, creating widgets and handling the program flow
- **variables.c** - Variable/state management; tracks widget values and exports them as shell variables on exit
- **signals.c** - Signal handler dispatch; evaluates conditional actions (if-true/if-false)
- **actions.c** - Executes action commands (shell commands, refresh, launch, etc.)
- **widgets.c** - Widget registry and lifecycle management
- **attributes.c / tag_attributes.c** - Attribute parsing for widget properties

### Widget Pattern
Each widget is in `src/widget_<name>.c/.h` (30+ widgets). Widgets follow a consistent pattern: creation function, attribute-setting function, signal connection, and value export.

### Known Limitations
- Nested `gtk_main()` loops in the `launch` action break AT-SPI for secondary windows, preventing automated testing of multi-window flows (TODO item 15)
- Text label wrapping (`<text wrap="true">`) does not work (TODO item 14)

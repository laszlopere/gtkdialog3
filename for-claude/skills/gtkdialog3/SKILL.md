---
name: gtkdialog3
description: >-
  Write, edit, and debug GtkDialog3 GUIs — desktop GTK3 dialogs described in an
  XML-like markup embedded in shell scripts and run with the `gtkdialog3` tool.
  Use whenever the task involves building a graphical dialog/front-end from a
  shell script, a `<window>`/`<vbox>`/`<entry>`/`<button>` markup, an exported
  `MAIN_DIALOG` variable passed to `gtkdialog3 --program=`, or reading widget
  values back into bash. Covers the widget set, the `<action>`/signal system,
  shell-variable export, and the non-obvious parser quirks.
---

# GtkDialog3

GtkDialog3 builds a GTK3 GUI from XML-like markup. You put the markup in an
exported shell variable, run `gtkdialog3 --program=THATVAR`, the tool draws the
window, and on exit it prints each named widget's value as a shell assignment
that the calling script `eval`s. It is the fastest way to give a shell script a
real desktop dialog. The binary here reports **version 0.9.0** (an extended
0.8.3 fork) and is invoked as `gtkdialog3`.

## Mental model

- **Markup → widgets.** The parser recognises a fixed set of widget tags
  (`<window>`, `<vbox>`, `<entry>`, `<button>`, …) and container tags. It is
  *XML-like, not XML* (see Critical rules).
- **`<variable>` is the wire.** Each interactive widget gets a `<variable>NAME</variable>`.
  That name is both how actions address the widget (`refresh:NAME`, `enable:NAME`)
  and the shell variable its value is exported to on exit. **No `<variable>` → the
  value is not exported.**
- **`<action>` is the behaviour.** Actions run on GTK signals. An action with no
  prefix is a shell command; a prefixed action (`exit:`, `refresh:`, `enable:`,
  `set:` …) calls a built-in. They run top-to-bottom like a tiny program.
- **Values flow through the shell.** Before any shell-command action runs (and on
  exit), all widget variables are exported to the environment, so `$NAME` inside an
  action reflects live widget state.
- **One script, one or more `<window>`s.** Extra windows live in their own
  exported variables and are opened with `launch:` / closed with `closewindow:`.

## Canonical script skeleton

```sh
#!/bin/sh
export MAIN_DIALOG='
<window title="Example" resizable="false">
  <vbox spacing="6" border-width="8">
    <frame title="Hostname">
      <entry>
        <default>localhost</default>
        <variable>ENTHOST</variable>
      </entry>
    </frame>
    <buttonbox layout="end">
      <button stock="cancel"></button>
      <button stock="ok"></button>
    </buttonbox>
  </vbox>
</window>'

gtkdialog3 --program=MAIN_DIALOG
```

## Capturing widget values back into the script

```sh
I=$IFS; IFS=""
for STATEMENTS in $(gtkdialog3 --program=MAIN_DIALOG); do
  eval "$STATEMENTS"
done
IFS=$I

[ "$EXIT" = "OK" ] && echo "Host is $ENTHOST"
```

`gtkdialog3` prints `NAME="value"` lines plus an `EXIT="…"` line (the stock
button name, or the `exit:` action's value). Setting `IFS=""` keeps spaces in
user input from being split. (For machine parsing, `--output-format=json|xml`
is also available.)

## Critical rules (these cause silent breakage or parse errors)

1. **No XML comments.** `<!-- … -->` is a *parse error*, as are `<?xml …?>`,
   `<!DOCTYPE>`, CDATA, namespaces, and entity references (`&lt;` `&amp;`). Put
   explanatory comments in the surrounding shell, never inside the markup.
2. **Escape literals with backslashes, not entities.** A literal `<` is `\<`,
   a literal `"` inside a quoted string is `\"`. `&lt;`/`&gt;`/`&amp;` do **not** work.
3. **Name every widget you need to read.** Unnamed widgets are not exported. Use
   `<variable>NAME</variable>`; add `export="false"` only if a name is needed
   internally (for `refresh:` etc.) but should stay out of the output.
4. **Actions run in `$SHELL`.** Shell functions used in `<action>`/`<input>` must
   be `export -f`'d, or sourced via `gtkdialog3 --include=funcs.sh`. Plain
   environment variables are already exported.
5. **Multi-window: the shell variable name must equal the window's `<variable>`.**
   `launch:winFoo` needs an exported `winFoo` containing a `<window>…<variable>winFoo</variable></window>`.
6. **Single-quote the markup in bash.** Use `'…'` so `$` and backticks are not
   expanded by bash; interpolate deliberately by closing/reopening quotes. Inside
   markup, prefer `"` for tag-attribute quoting.

## Workflow for authoring a dialog

1. Pick widgets from `reference/widgets.md`; pick behaviours from `reference/actions-signals.md`.
2. Write the skeleton above; name every interactive widget.
3. **Validate the markup without a display:** `gtkdialog3 --program=MAIN_DIALOG --print-ir`
   parses and prints the instruction list, then exits — a fast syntax check.
4. Run it for real to see the window; capture values with the loop above.
5. If something behaves oddly, check `reference/gotchas.md` before assuming a bug —
   most surprises are documented parser/automaton behaviour.

## Reference files (load on demand)

- `reference/widgets.md` — every widget & container: tag, what it exports, key
  attributes, sub-elements, signals.
- `reference/actions-signals.md` — the full action vocabulary (24 built-ins),
  action/signal/condition syntax, and the special `$PTR_*`/`$KEY_*` variables.
- `reference/gotchas.md` — non-obvious behaviours verified against the C source,
  with `file:line` citations.
- `reference/templates.md` — complete, runnable starting points (entry form,
  conditional enable/disable, dynamic list, progress bar, two windows).

Authoritative in-tree sources if you need more than the above: the manual
`doc/gtkdialog.texi`, the per-widget pages in `doc/reference/*.html`, and the
226 runnable scripts under `examples/`.

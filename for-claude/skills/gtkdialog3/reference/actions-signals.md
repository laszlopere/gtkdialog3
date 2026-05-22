# Actions, signals & conditions

Behaviour is attached to widgets with `<action>` elements. They run in document
order when a triggering signal fires — a small sequential program per signal.

## Action syntax

Two equivalent forms (action type is case-insensitive):

```xml
<action>type:argument</action>                 <!-- colon syntax -->
<action function="type">argument</action>      <!-- attribute syntax -->
```

`function="..."` is also accepted as `type="..."`. Use the attribute form when you
need the extra attributes:

- `signal="GTK-SIGNAL"` — which signal triggers this action (default depends on the
  widget, e.g. `clicked` for buttons, `changed` for entries, `toggled` for toggles).
- `condition="EXPR"` — the action runs only if EXPR is true (see Conditions). Note
  the condition is **evaluated every time the signal fires** — if it's `command_is_true(...)`
  the shell command runs (and can have side effects) on each fire.

An action with **no recognised prefix is a shell command.** A `type:` whose prefix is
not one of the built-ins below is also treated as a shell command (the `:` is kept).

## Shell-command actions

No prefix → run the text in the user's `$SHELL` (fallback `/bin/sh`). Before it runs,
**all widget variables are exported** to the environment, so `$NAME` is the live value.
With `gtkdialog3 --include=file`, that file is dot-sourced first. Append `&` to run in
the background instead of blocking the GUI.

```xml
<entry><variable>NAME</variable></entry>
<button>
  <label>Greet</label>
  <action>notify-send "Hello $NAME"</action>
  <action>echo "Hello $NAME" > /tmp/out &</action>
</button>
```

Inside action text, shell `>` and `&` are written **raw** (they are not special to
the parser, which only stops at `<`). Do not use `&gt;`/`&amp;` — entities are passed
through literally and break the command. A literal `<` in a command must be `\<`.

## Built-in action functions (24)

Exact prefixes, from `src/stringman.c:306`. `Name` is a widget/window `<variable>`.

| Action | Effect |
|---|---|
| `exit:Value` | Close dialog; print all variables + `EXIT="Value"` |
| `launch:Name` | Open the window stored in exported var `Name` (raises it if already open) |
| `closewindow:Name` | Close that window; if it was the last, the program exits |
| `presentwindow:Name` | Raise an already-open window and focus it (no new window) |
| `enable:Name` | Make the widget sensitive (interactive) |
| `disable:Name` | Grey out the widget |
| `show:Name` | Make the widget visible |
| `hide:Name` | Hide the widget (keeps its value) |
| `activate:Name` | Simulate user activation → fires that widget's own actions |
| `grabfocus:Name` | Give keyboard focus to the widget |
| `refresh:Name` | Re-evaluate the widget's `<input>` and update it (exports vars first) |
| `save:Name` | Write the widget value to its `<output type="file">` |
| `fileselect:Name` | Open a file chooser, put the path into the widget (see fs-* attrs) |
| `clear:Name` | Remove all content/rows/items from the widget |
| `removeselected:Name` | Remove the selected row (list/tree/table) or selected text (edit) |
| `set:Widget.prop=Value` | Set a GTK property at runtime (e.g. `set:win.title=Busy`) |
| `break` | Stop the rest of this action chain (usually with a `condition`) |
| `cut:Name` `copy:Name` `paste:Name` `selectall:Name` | Clipboard ops on `<edit>` |
| `insert:Src,Target` `append:Src,Target` | Copy Src widget's value into Target — **barely implemented; avoid** (`src/actions.c:861`) |

`removeselected` has **no hyphen** (not `remove-selected`). `set:` also drives the
synthetic properties of optional widgets: `set:term.command=…`, `set:src.file=…`,
`set:src.language=sh`, `set:web.uri=…`.

### Conditional toggle actions (toggle widgets only)

On `<checkbox>`, `<radiobutton>`, `<togglebutton>`, `<expander>`, and check
`<menuitem>`, an action may be prefixed with `if true` / `if false` to run only in
that state (`src/signals.c:1087`):

```xml
<checkbox>
  <variable>CB</variable>
  <action>if true enable:ENTRY</action>
  <action>if false disable:ENTRY</action>
</checkbox>
```

## Conditions

`condition="…"` accepts these predicates (`src/signals.c:68`), each with a
`*_is_true` and `*_is_false` form:

| Predicate | True when |
|---|---|
| `command_is_true(CMD)` / `_false` | shell CMD exits 0 |
| `file_is_true(PATH)` / `_false` | file exists / is readable |
| `active_is_true(VAR)` / `_false` | toggle widget VAR is on |
| `sensitive_is_true(VAR)` / `_false` | widget VAR is enabled |
| `visible_is_true(VAR)` / `_false` | widget VAR is shown |

```xml
<action condition="active_is_true(CHECKBOX)" function="break">""</action>
```

## Signals you can use in `signal="…"`

Wired in `src/widget_*.c` / `src/signals.c`. The useful set:

`clicked`, `pressed`, `released`, `activate`, `changed`, `toggled`, `value-changed`,
`color-set`, `font-set`, `cursor-changed`, `row-activated`, `button-press-event`,
`button-release-event`, `enter-notify-event`, `leave-notify-event`, `key-press-event`,
`key-release-event`, `focus-in-event`, `focus-out-event`, `realize`, `map`,
`delete-event`, `icon-press`, `icon-release`, `file-changed` (from `<input type="file">`),
`child-exited` (terminal).

## Special variables inside a signal handler

While an action triggered by a mouse/key signal runs, these are set in the
environment and **unset again afterwards** — they only exist during that handler
(`src/signals.c:267` mouse, `:533` keyboard):

- Mouse: `$PTR_X`, `$PTR_Y`, `$PTR_X_ROOT`, `$PTR_Y_ROOT`, `$PTR_BTN`, `$PTR_MOD`
  (and deprecated `$BUTTON`).
- Keyboard: `$KEY_VAL`, `$KEY_SYM`, `$KEY_UNI`, `$KEY_MOD`, `$KEY_RAW`.

```xml
<eventbox>
  <text><label>Click me</label></text>
  <action signal="button-press-event">echo "button $PTR_BTN at $PTR_X,$PTR_Y"</action>
</eventbox>
```

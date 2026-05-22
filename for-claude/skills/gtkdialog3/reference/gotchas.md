# Gotchas — non-obvious behaviour

Each item verified against this tree's source or manual. Citations are `file:line`.
These are the things that look like bugs but are how GtkDialog3 actually works.

## Parsing

- **It is not XML.** XML comments `<!-- -->`, `<?xml?>`, `<!DOCTYPE>`, CDATA,
  namespaces, and entity references (`&lt;`, `&amp;`, `&quot;`) all cause a parse
  error. (`doc/gtkdialog.texi:249`). Keep comments in the surrounding shell.
- **Escaping is backslash, not entity.** `\<` `\>` `\"` `\\` are the only escapes;
  the lexer strips them via `strip_backslash_escapes()` (`src/gtkdialog_lexer.l:60`).
- **The root `<window>` can be omitted** — the parser wraps loose content in an
  implicit window (`doc/gtkdialog.texi:219`). Prefer writing it explicitly anyway.
- **Imperative constructs exist but are deprecated** (`<command assignment>`, `<if>`,
  `<while>`, `<show/>`) for parse-time generation (`doc/gtkdialog.texi:183`). Generate
  markup in bash instead of relying on these.

## Variables & export

- **Values are exported only at action/refresh/exit time, not continuously.**
  `variables_export_all()` is called from shell-command actions (`src/actions.c:654`),
  `refresh:` (`src/actions.c:837`), `launch:` (`src/actions.c:221`), condition
  evaluation (`src/signals.c:1336`), and at exit. A `$VAR` read outside those moments
  may be stale.
- **Unnamed widgets are not exported.** No `<variable>` → the value never reaches the
  script (`doc/gtkdialog.texi:1912`). Auto-generated internal names use a single global
  counter, `"%s%03d"` (`src/stringman.c:527`) — don't rely on guessing them.
- **`export="false"`** keeps a named widget addressable by actions but out of the
  output (`doc/gtkdialog.texi:1915`).

## Actions

- **Action prefix is `removeselected`, not `remove-selected`** (`src/stringman.c:322`).
  An unknown prefix is silently treated as a shell command, so a typo'd built-in just
  runs in the shell and "does nothing" (`src/stringman.c:372`).
- **`insert:`/`append:` are stubs.** Work was started but not finished; both call the
  same incomplete code (`src/actions.c:861`). Don't depend on them.
- **`condition="command_is_true(...)"` runs the command on every signal fire** — it
  exports all vars and executes the shell command each time (`src/signals.c:1333`),
  so conditions with side effects fire repeatedly.
- **Inline `if true`/`if false` only works on toggle widgets** (checkbox, radiobutton,
  togglebutton, expander, check-menuitem) — it's gated on the widget having an
  active state (`src/signals.c:1086`). On other widgets use `condition=` instead.
- **`exit:` has an undocumented raw form:** `exit:=VALUE` prints `EXIT=VALUE` without
  quotes, vs the normal `EXIT="VALUE"` (`src/actions.c:240`).
- **`$PTR_*` / `$KEY_*` exist only inside their signal handler** — set on entry, unset
  on exit (`src/signals.c:267`, `:533`). They are empty in unrelated actions.

## Shell execution

- **Actions/inputs run in `$SHELL`, not `/bin/sh`,** specifically so `export -f` bash
  functions survive (plain `system()` would lose them) (`src/actions.c:50`). Still:
  a function used in an action must be `export -f`'d or provided via `--include`.

## Widget-specific

- **Multi-window needs name == name.** `launch:Foo`/`closewindow:Foo` look the window
  up by the variable name (`src/actions.c` `action_launchwindow`/`action_closewindow`),
  so the exported shell variable, the `--program` target, and the window's
  `<variable>` must all be the identical string (`doc/gtkdialog.texi:764`).
- **Progressbar input is a stream, not a percentage attribute.** Its `<input>` runs in
  a background thread; each output line that parses as a number 0–100 sets the bar,
  each non-numeric line sets the bar text, and hitting 100 fires the actions
  (`src/widget_progressbar.c:312`).
- **Tree/table columns are pipe-separated** in both `<label>` headers and `<item>`
  rows; the parser splits on `|` (`src/widget_tree.c:981`). A literal `|` in data is
  not directly supported.
- **`<input type="file">` watches the file.** Editing it on disk emits `file-changed`,
  which you can wire to `refresh:` for live updates (`doc/gtkdialog.texi:1997`).
- **`<output>` is a file destination, not live output.** It only does something with
  `type="file"` and the `save:` action (`doc/gtkdialog.texi:2030`).
- **`<timer>` runs only while sensitive.** `disable:`/`enable:` stop and restart it;
  hide its stub label with `visible="false"` (`doc/gtkdialog.texi:1460`).

## Build / availability

- **`<terminal>`, `<sourceview>`, `<webview>` are optional**, compiled only if VTE /
  GtkSourceView / WebKitGTK were present at build time. Check `gtkdialog3 --version`
  before using them (`doc/gtkdialog.texi:1536`).

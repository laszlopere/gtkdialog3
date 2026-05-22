# Widgets & containers

Distilled from `doc/gtkdialog.texi` and verified against `src/widget_*.c`. "Exports"
is the string put into the widget's `<variable>` on exit / when actions run.

## How attributes work

Two ways to configure a widget:

- **Tag attributes** on the opening tag — `<entry width-request="300" visible="false">`.
  Any attribute whose name matches a **GObject property** of the underlying GTK widget
  is applied directly (so any GTK3 property works without explicit support). Booleans
  take `true`/`false`; enums take the GLib nick (`start`, `center`, `end`, `fill`).
  Common ones: `halign`/`valign`, `hexpand`/`vexpand`, `margin-start`/`-end`/`-top`/`-bottom`,
  `width-request`/`height-request`, `sensitive`, `visible`, `tooltip-text`.
- **Sub-elements** between the tags — `<variable>`, `<label>`, `<default>`, `<input>`,
  `<output>`, `<item>`, `<sensitive>`, `<width>`/`<height>`, `<action>`. See
  `actions-signals.md` and the sub-element notes at the bottom.

Packing (how a child takes space in its box): `space-expand="true"` requests extra
space, `space-fill="true"` fills it. Set per-widget or globally via `--space-expand`/`--space-fill`.

## Display & text input

| Tag | Purpose | Exports | Notable |
|---|---|---|---|
| `<text>` | Static label | displayed text | `use-markup="true"` for Pango markup; `<input>` makes it dynamic (refreshable) |
| `<entry>` | Single-line text field | current text | `<sensitive>password</sensitive>` masks input; fires on change & Enter |
| `<edit>` | Multi-line text editor | full buffer text | `<input type="file">` loads, `<output type="file">`+`save:` writes; supports `cut:/copy:/paste:/selectall:` |
| `<pixmap>` | Static image | (none) | `<input type="file">img.png`; searches `$GTKDIALOG_PIXMAP_PATH`; `refresh:` reloads |

## Toggles & buttons

| Tag | Purpose | Exports | Notable |
|---|---|---|---|
| `<button>` | Pushbutton | (none) | `<button stock="ok\|cancel\|help\|yes\|no">`; no action → clicking exits with `EXIT=`label; icon via `<input type="stock">` |
| `<togglebutton>` | Stays pressed | `true`/`false` | `<default>true</default>`; fires `toggled` |
| `<checkbox>` | Check mark | `true`/`false` | supports inline `if true …`/`if false …` actions |
| `<radiobutton>` | Exclusive choice | `true`/`false` | auto-groups with adjacent radiobuttons |
| `<switch>` | Modern on/off slider | `true`/`false` | like checkbox |

Stock buttons set `EXIT` to `OK`/`Cancel`/`Help`/`Yes`/`No` and close the dialog.

## Choosers (drop-downs)

| Tag | Purpose | Exports | Notable |
|---|---|---|---|
| `<comboboxtext>` | Fixed drop-down (choose only) | selected item text | items via `<item>` / `<input>`; `<default>` pre-selects by text |
| `<comboboxentry>` | Drop-down + editable entry | current text | variant of comboboxtext; `activate` signal on Enter |
| `<combobox>` | Editable drop-down | typed/selected text | items via `<item>`/`<input>` |
| `<colorbutton>` | Colour picker | `#rrggbb` (or `#rrggbb\|alpha` with `use-alpha="true"`) | `<default>#4488cc</default>`; fires `color-set` |
| `<fontbutton>` | Font picker | Pango font string | `font-name="Monospace 18"`; fires `font-set` |

## Numbers / ranges

| Tag | Purpose | Exports | Notable |
|---|---|---|---|
| `<spinbutton>` | Numeric entry + arrows | numeric value | `range-min`/`range-max`/`range-step`/`range-value` |
| `<hscale>` / `<vscale>` | Slider | numeric value | same `range-*` attrs; `<item>` adds scale marks |
| `<progressbar>` | Progress indicator | (none) | `<input>` streams numbers 0–100 (text lines update the label); reaching 100 fires the actions — see gotchas |

## Lists, tables, trees

| Tag | Purpose | Exports | Notable |
|---|---|---|---|
| `<list>` | Single-column list | selected row text | rows via `<item>` or one-per-line `<input>`; `selected-row="N"` |
| `<table>` | Sortable multi-column table | selected cell from `exported-column` (default 0); multi-select → newline-separated | `<label>` = pipe-separated headers; `<item>`/`<input>` rows pipe-separated; `selection-mode`, `column-visible`, `column-header-active`, `sort-function` |
| `<tree>` | Multi-column tree view | selected row | like table but older; `<label>` pipe headers, `<item>` pipe rows; row icons via `<item stock="…">`/`<item icon="…">`, `<input icon-column="N">`/`stock-column="N"` |

Column data everywhere in tree/table is **pipe (`|`) separated**.

## Containers (every widget must live in one)

| Tag | Purpose | Notable |
|---|---|---|
| `<window>` | Top-level | `title`, `icon-name`; holds one child; `<variable>` names it for `launch:`/`closewindow:` |
| `<vbox>` / `<hbox>` | Vertical / horizontal box | `spacing` (default 5), `homogeneous`, `border-width`, `space-expand`/`space-fill` |
| `<frame>` | Bordered group with title | `title="…"` (or dynamic via `<input>`) |
| `<notebook>` | Tabbed pages | each direct child = a page; `labels="A\|B\|C"` tab titles; exports current page index (from 0) |
| `<expander>` | Collapsible section | `expanded="true"`; `<label>` is the header; exports `true`/`false` |
| `<eventbox>` | Invisible event catcher | wraps one child to capture `button-press-event`/`enter-notify-event`/key events on widgets that don't emit them |
| `<buttonbox>` | Standard button row | `layout="spread\|edge\|start\|end\|center"` (default end), `orientation` |

## Menus

`<menubar>` → `<menu>` (with a `<label>` title) → `<menuitem>` (with `<label>`,
`<variable>`, `<action>`). `<menuitemseparator></menuitemseparator>` inserts a divider.
A `<menuitem checkbox="true" label="…">` is a checkable item that exports `true`/`false`
and supports inline `if true`/`if false` actions.

## Other / status

| Tag | Purpose | Exports | Notable |
|---|---|---|---|
| `<statusbar>` | Message bar | current message | set via `<label>`/`<default>`/`<input>` |
| `<timer>` | Invisible periodic trigger | `true`(running)/`false` | `interval` (default 1), `milliseconds="true"`; runs while sensitive — `disable:`/`enable:` stop/start it; use `visible="false"`; actions fire each tick (commonly `refresh:`) |
| `<hseparator>` / `<vseparator>` | Decorative line | (none) | no value/actions |

## Optional widgets (require build-time libraries — check `gtkdialog3 --version`)

| Tag | Needs | Exports | Notable |
|---|---|---|---|
| `<terminal>` | VTE 2.91 | child PID | spawns a shell; `argv0…argvN` set the command; feed input with `set:NAME.command=…` |
| `<sourceview>` | GtkSourceView 4 | buffer text | syntax highlight via `language="c\|sh\|python\|json"`; `set:NAME.file=…`, `set:NAME.language=…` |
| `<webview>` | WebKitGTK | current URI | `<default>` initial URL; navigate with `set:NAME.uri=…` |

## Sub-element semantics worth knowing

- **`<variable>`** — names the widget; `export="false"` keeps it internal (addressable
  by actions, omitted from output). Unnamed → not exported.
- **`<label>`** — meaning is widget-specific: button caption, checkbox text, frame title,
  window title, tree/table pipe-separated headers, progressbar text, statusbar message.
- **`<default>`** — initial value: entry text, toggle `true`/`false`, combobox selection,
  numeric value, colour `#rrggbb`, font, webview URL.
- **`<input>`** — `type="bash"` (default; run a command), `type="file"` (read a file,
  *and watch it* → `file-changed` signal), `type="stock"` (GTK stock icon id like
  `gtk-open`), `type="icon"` (theme icon name). `refresh:` re-evaluates it.
- **`<output type="file">path`** — destination written by the `save:` action.
- **`<item>`** — option for combos/list; pipe-separated row for tree/table; mark for scales.
- **`<sensitive>`** — `true`/`false`/`enabled`/`disabled`/`yes`/`no`/`0`, plus
  `password` for entries. Legacy `<visible>` is an alias.
- **`<width>`/`<height>`** — minimum size in px (character cols/rows for `<terminal>`);
  equivalent to `width-request`/`height-request` tag attributes.

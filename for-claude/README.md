# for-claude — a GtkDialog3 skill for Claude Code

[Claude Code](https://claude.com/claude-code) is Anthropic's AI coding assistant
that runs in your terminal. A *skill* is a folder of instructions you can give it
so it becomes an expert on a specific topic — here, building GtkDialog3 GUIs. With
this installed you can ask in plain language ("make a dialog with a dropdown and a
Save button") and let the assistant write the markup for you.

This directory packages everything an AI coding assistant needs to write **correct**
GtkDialog3 GUIs — the XML-like markup, run with `gtkdialog3`, that gives shell
scripts real GTK3 dialogs. New to all this? You don't have to be: the reference
files are plain Markdown and read fine as a human cheat sheet too.

The content is distilled from this project's manual (`doc/gtkdialog.texi`), the
per-widget reference (`doc/reference/*.html`), the 226 example scripts under
`examples/`, and the C source — including parser/automaton behaviours you can't
guess from the markup alone. It targets **this tree's build** (`gtkdialog3`,
version 0.9.0, an extended 0.8.3 fork).

## Install (drop it into another project)

Copy the skill into the project's `.claude/skills/`:

```sh
cp -r for-claude/skills/gtkdialog3 /path/to/your/project/.claude/skills/
```

Claude Code auto-loads the skill when a task mentions building a GtkDialog
dialog/front-end. To make it available in **every** project, copy it to
`~/.claude/skills/gtkdialog3` instead.

## What's inside

```
skills/gtkdialog3/
  SKILL.md                     # mental model, the canonical script idiom, critical rules
  reference/
    widgets.md                 # every widget & container: tag, exported value, attributes
    actions-signals.md         # the 24 action functions, signals, conditions, $PTR_*/$KEY_*
    gotchas.md                 # non-obvious behaviour, each cited to file:line
    templates.md               # complete runnable starting points
```

`SKILL.md` stays lean and always-loaded; the `reference/` files are pulled in only
when needed.

## Use without installing

The reference files are plain Markdown, so you can also `@`-mention them
(`@for-claude/skills/gtkdialog3/SKILL.md`) or paste a section into context without
installing the skill.

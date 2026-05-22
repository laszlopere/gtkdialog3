# Worked example: building a system dashboard with a Claude Code agent

This shows how to drive [Claude Code](https://claude.com/claude-code) to build a
**non-trivial** GtkDialog3 app — not a one-widget toy — by handing the design work
to a sub-agent and letting the main session assemble and verify the result. The
finished program is [`system_dashboard`](system_dashboard) in this folder.

It assumes the `gtkdialog3` skill is installed (see [`../../README.md`](../../README.md)).

## The prompt

Paste this into Claude Code from anywhere in a project that has the skill installed:

```text
Use the gtkdialog3 skill to build a system-monitor dashboard as a single,
self-contained bash script called `system_dashboard`.

First, launch a Plan agent to design it. Tell that agent to read the skill's
reference/widgets.md, reference/actions-signals.md and reference/gotchas.md
first, then return concrete markup decisions (which widgets, how data flows,
which column is exported) for this spec:

  - One window, a notebook with three tabs:
      • Processes — a tree of PID / CPU% / MEM% / Command, busiest first,
        with a Refresh button, a "Kill selected" button, and a checkbox that
        toggles a 2-second auto-refresh timer.
      • Disk — a tree of `df -hP`.
      • System — host, kernel, uptime and memory, each refreshable.
  - A statusbar showing the process count and the last-updated time.
  - A "Refresh all" and a "Quit" button along the bottom.

Then implement the agent's design following SKILL.md's canonical skeleton.
Put every data command that needs quotes (the ps/df/awk pipelines) in an
exported shell function called via `bash -c name`, because the markup is a
single-quoted string and can't contain single quotes.

Before telling me it's done: run `gtkdialog3 --program=MAIN_DIALOG --print-ir`
to confirm it parses, then launch it to confirm the tabs populate and the
statusbar updates.
```

## Why route the design through an agent

The dashboard touches a dozen widgets and several skill rules at once. Asking a
**Plan/Explore sub-agent** to read the reference files and return the design has two
benefits:

- **The main session stays lean.** The agent absorbs the reference reading and hands
  back only the conclusions, so the context that writes the code isn't full of
  documentation.
- **Decisions are made before code.** The agent settles the load-bearing choices —
  *tree vs table*, *which column to export so "Kill selected" gets the PID*, *timer
  vs polling* — so implementation is mechanical rather than guess-and-check.

For a one-widget dialog this is overkill; reach for an agent when the GUI has
multiple panes, live data, and interacting controls — exactly this case.

## What the agent has to get right (and where the skill tells it)

| Design decision | Skill source |
|---|---|
| Tabs = a `<notebook labels="…">` with one child per page | `reference/widgets.md` (Containers) |
| `<tree exported-column="0">` so the selected **PID** lands in `$PROCTREE` | `reference/widgets.md` (lists/trees) |
| `[ -n "$PROCTREE" ] && kill "$PROCTREE"` then `refresh:` — vars are live in actions | `reference/actions-signals.md` |
| Auto-refresh = a `<timer>` that a checkbox `enable:`/`disable:`s (it runs while sensitive) | `reference/widgets.md` + `gotchas.md` |
| `ps … \| awk '…'` lives in an exported function, not inline | `gotchas.md` (single-quoted markup can't hold `'`) |
| Verify with `--print-ir` before launching | `SKILL.md` (workflow) |

## What you get

The resulting [`system_dashboard`](system_dashboard) is a ~120-line bash script.
Run it:

```sh
./system_dashboard            # launch the GUI
./system_dashboard --check    # parse-check only (gtkdialog3 --print-ir), no window
./system_dashboard --dump     # print the generated markup
```

The Processes tab shows a live, CPU-sorted process list that refreshes every two
seconds; the statusbar tracks the process count and update time; the Disk and
System tabs populate from `df` and `uname`/`uptime`/`free`. It was built and run
exactly this way, and verified to launch and populate before being committed.

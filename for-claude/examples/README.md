# Worked examples

These show the `gtkdialog3` skill in action — real prompts you can give an AI
assistant, paired with the verified app each one produces. They complement the
project's per-widget scripts under the top-level [`examples/`](../../examples/),
which are smaller and focused on a single widget.

| Example | What it demonstrates |
|---|---|
| [`login-dialog/`](login-dialog/) | The simplest case: one plain-language request → a runnable login dialog (username, masked password, OK/Cancel). Shown on the project's main README. |
| [`system-dashboard/`](system-dashboard/) | Driving a Claude Code **agent** to design and build a non-trivial, multi-tab app (live process list with auto-refresh and "kill selected", disk usage, system info). See its [`PROMPT.md`](system-dashboard/PROMPT.md). |

The bigger examples include a `PROMPT.md` (the prompt to give the assistant, plus
how the agent workflow goes) alongside the finished, runnable program.

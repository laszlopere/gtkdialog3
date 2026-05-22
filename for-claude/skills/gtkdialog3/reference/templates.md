# Templates

Complete, runnable starting points. Each is a full script: save it, `chmod +x`, run.
All markup is single-quoted so bash leaves `$` and backticks alone. Validate any edit
with `gtkdialog3 --program=MAIN_DIALOG --print-ir` before launching.

## 1. Entry form + value capture

The everyday pattern: collect input, read it back into the script.

```sh
#!/bin/sh
export MAIN_DIALOG='
<window title="Login" resizable="false">
  <vbox spacing="6" border-width="8">
    <frame title="Credentials">
      <hbox>
        <text><label>User:</label></text>
        <entry><variable>LOGIN</variable></entry>
      </hbox>
      <hbox>
        <text><label>Pass:</label></text>
        <entry><sensitive>password</sensitive><variable>PASS</variable></entry>
      </hbox>
    </frame>
    <buttonbox layout="end">
      <button stock="cancel"></button>
      <button stock="ok"></button>
    </buttonbox>
  </vbox>
</window>'

I=$IFS; IFS=""
for STATEMENTS in $(gtkdialog3 --program=MAIN_DIALOG); do eval "$STATEMENTS"; done
IFS=$I

if [ "$EXIT" = "OK" ]; then
  echo "User=$LOGIN"
else
  echo "Cancelled."
fi
```

## 2. Checkbox driving enable/disable

Inline `if true`/`if false` actions on a toggle widget gate other widgets live.

```sh
#!/bin/sh
export MAIN_DIALOG='
<window title="Options">
  <vbox spacing="6" border-width="8">
    <checkbox>
      <label>Use a custom path</label>
      <variable>CUSTOM</variable>
      <action>if true enable:APP_PATH</action>
      <action>if false disable:APP_PATH</action>
    </checkbox>
    <entry>
      <variable>APP_PATH</variable>
      <default>/opt/app</default>
      <sensitive>false</sensitive>
    </entry>
    <button stock="ok"></button>
  </vbox>
</window>'

gtkdialog3 --program=MAIN_DIALOG
```

## 3. Dynamic list with refresh

`<input>` populates the list from a command; a button re-runs it with `refresh:`.

```sh
#!/bin/sh
export MAIN_DIALOG='
<window title="Processes">
  <vbox spacing="6" border-width="8">
    <list>
      <variable>PROC</variable>
      <height>200</height><width>300</width>
      <input>ps -eo comm= | sort -u</input>
      <action>echo "Selected: $PROC"</action>
    </list>
    <hbox>
      <button>
        <label>Reload</label>
        <action>refresh:PROC</action>
      </button>
      <button stock="ok"></button>
    </hbox>
  </vbox>
</window>'

gtkdialog3 --program=MAIN_DIALOG
```

## 4. Progress bar with a background task

The `<input>` streams numbers 0–100; reaching 100 fires the `exit:` action.

```sh
#!/bin/sh
export MAIN_DIALOG='
<window title="Working">
  <vbox spacing="6" border-width="8">
    <text><label>Processing files...</label></text>
    <progressbar>
      <label>Starting</label>
      <input>for i in $(seq 0 20 100); do echo $i; echo "# step $i"; sleep 0.3; done</input>
      <action function="exit">Done</action>
    </progressbar>
    <button stock="cancel"></button>
  </vbox>
</window>'

gtkdialog3 --program=MAIN_DIALOG
```

## 5. Two windows (launch / closewindow)

Each window is its own exported variable whose name equals its `<variable>`.

```sh
#!/bin/sh
export winMain='
<window title="Main">
  <vbox spacing="6" border-width="8">
    <button>
      <label>Open settings</label>
      <action function="launch">winSettings</action>
    </button>
    <button>
      <label>Quit</label>
      <action function="exit">Quit</action>
    </button>
  </vbox>
</window>'

export winSettings='
<window title="Settings">
  <vbox spacing="6" border-width="8">
    <checkbox><label>Verbose</label><variable>VERBOSE</variable></checkbox>
    <button>
      <label>Close settings</label>
      <action function="closewindow">winSettings</action>
    </button>
  </vbox>
  <variable>winSettings</variable>
</window>'

gtkdialog3 --program=winMain
```

> The main window does not need its own `<variable>` unless another window targets
> it; `winSettings` does, because `launch:`/`closewindow:` look it up by that name.

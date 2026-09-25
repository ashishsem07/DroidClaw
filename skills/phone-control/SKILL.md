---
name: phone-control
description: >-
  Control a real Android phone connected to this machine (USB or same Wi-Fi) - take
  screenshots, read the UI tree, tap, swipe, scroll, type, press Back/Home, open apps and
  deep links, wake and unlock - through the DroidClaw ADB bridge. Use whenever a task needs
  an agent to operate a physical Android device or a mobile app.
---

# Phone control (DroidClaw bridge)

This file is written for any AI agent (Claude Code, Codex, Cursor, a custom tool-using
agent). It needs nothing but a shell. Paths below are relative to the DroidClaw repo root.

## 1. Make sure the bridge is up

```bash
local-bridge/phonectl health
```

- `UP ...` means you are ready. If it says `ASLEEP` or `locked`, run `local-bridge/phonectl unlock`.
- `cannot reach the bridge` means start it (leave it running in its own terminal/background job):
  `local-bridge/start-bridge.sh`
- `NO DEVICE` means the phone is not attached. Ask the human to plug it in and accept the
  "Allow USB debugging" prompt, then run `local-bridge/phonectl reconnect`.

## 2. The loop

Every phone task is the same four steps, repeated:

1. **Look**: `local-bridge/phonectl shot` saves a PNG (default `/tmp/phone.png`) and prints the path.
   Open/read that image to see the screen.
2. **Locate**: `local-bridge/phonectl ui [filter]` lists labelled elements as
   `(TAP) (x,y) label`. Use these coordinates instead of guessing from pixels.
3. **Act**: tap, type, swipe, or press a key.
4. **Verify**: screenshot again before assuming the action worked. Wait ~1-2 s after
   actions that load something.

## 3. Commands

```bash
P=local-bridge/phonectl
$P health                       # attached? battery? screen asleep/locked?
$P unlock                       # wake + dismiss lockscreen (PIN from PHONE_PIN on the bridge)
$P shot [out.png]               # screenshot
$P ui [substring]               # (TAP) (x,y) label  - filter by substring
$P tap 540 1200
$P swipe 540 1700 540 700 300   # x1 y1 x2 y2 [ms]
$P scroll down | up
$P type "hello world" [--clear] # types into the focused field
$P enter | back | home | recents
$P key 67                       # any Android keycode (67=backspace)
$P open com.android.chrome      # launch by package name
$P deeplink "https://example.com" [package]
$P reconnect                    # re-attach after unplug / Wi-Fi drop
```

Finding a package name: `adb shell pm list packages | grep -i <name>`.

## 4. Raw HTTP (if you cannot run the CLI)

The bridge is a REST API on `http://localhost:8723/v1`, compatible with the MobileRun v1
API. The device id in the path is ignored, so `local` works.

```bash
B=http://localhost:8723/v1/devices/local
curl -s http://localhost:8723/v1/health
curl -s "$B/screenshot?max_height=1600" -o /tmp/phone.png
curl -s "$B/ui-state?filter=true"                                  # {"a11y_tree": {...}}
curl -s -X POST "$B/tap"      -d '{"x":540,"y":1200}'
curl -s -X POST "$B/swipe"    -d '{"startX":540,"startY":1700,"endX":540,"endY":700,"duration":300}'
curl -s -X POST "$B/keyboard" -d '{"text":"hello world","clear":true}'
curl -s -X POST "$B/global"   -d '{"action":1}'                    # 1=Back 2=Home 3=Recents
curl -s -X POST "$B/key"      -d '{"keycode":66}'
curl -s -X PUT  "$B/apps/com.android.chrome"
curl -s -X POST "$B/deeplink" -d '{"url":"https://example.com"}'
curl -s -X POST "$B/unlock"
```

If the bridge was started with `PHONE_BRIDGE_TOKEN`, add
`-H "Authorization: Bearer $PHONE_BRIDGE_TOKEN"` to every call (the CLI does this from the
same env var).

## 5. Gotchas

- **Black screenshot or empty `ui`**: the screen is off. `phonectl unlock`.
- **Typing**: `input text` is ASCII only; emoji and non-Latin scripts are dropped. A leading
  `#` can be swallowed, and some keyboards autocorrect. Screenshot after typing, before sending.
- **Field not focused**: tap the field first, then `type`.
- **`ui` is empty but the screen is on**: some screens (games, video, canvas UIs) expose no
  accessibility labels. Fall back to reading the screenshot and tapping by coordinates.
  Screenshot pixels match tap coordinates only at full size; the `ui` coordinates always match.
- **Stale screen**: after navigation, wait 1-2 s before `ui`, or you get the previous screen.
- **Context size**: screenshots are large. Keep only the latest few in context.

## 6. Safety

- Do not uninstall apps, change system settings, sign out of accounts, or delete data unless
  the human asked for exactly that.
- Anything that posts, sends, pays, or messages another person is outward-facing: confirm
  with the human before the final tap unless they already told you to go ahead.
- `shell` access is off by default. Do not ask the human to enable it unless a task truly
  needs it.

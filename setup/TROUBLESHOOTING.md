# Troubleshooting

## Phone Connection Issues

### "Device not found" or "disconnected"
1. Run `local-bridge/phonectl health`. It tells you whether the bridge is up, whether a device is attached, and whether the screen is asleep.
2. `cannot reach the bridge`: start it with `local-bridge/start-bridge.sh`.
3. `NO DEVICE`: check `adb devices`. Replug the cable and accept the "Allow USB debugging" prompt. Over Wi-Fi, re-run `adb connect <ip>:5555`. Then `local-bridge/phonectl reconnect`.
4. Shows `unauthorized`: accept the prompt on the phone (tick "Always allow from this computer").

### Phone screen went dark / locked
Symptom: all-black screenshots and an empty UI tree. Run `local-bridge/phonectl unlock`. It wakes the screen, swipes the lockscreen away, and enters a PIN if you started the bridge with `PHONE_PIN=1234` (or wrote it to `~/.phone-bridge/pin`). The PIN never leaves your machine. To prevent it recurring:
1. Make sure "Stay awake" is enabled in Developer Options
2. Make sure the phone is plugged in (Stay awake only works while charging)

### Text types wrong or not at all
`input text` is ASCII only: emoji and non-Latin scripts are dropped, a leading `#` can be swallowed, and some keyboards autocorrect. Tap the field first, type, then screenshot before sending. For full Unicode install [ADBKeyboard](https://github.com/senzhk/ADBKeyBoard).

### Screenshots are large
Install Pillow (`pip install pillow`) and the bridge downscales on `?max_height=1600` (the CLI default). Without it you get full resolution.

### `shell endpoint is disabled`
Working as intended. It is arbitrary command execution, so it is off unless you start the bridge with `PHONE_BRIDGE_ALLOW_SHELL=1`.

### Rate limit errors
The local bridge has no rate limits. The legacy MobileRun cloud API does; against it the agent automatically:
- Waits 2 seconds between API calls
- Retries up to 3 times with 10-second waits on rate limit errors

If you hit persistent rate limits, slow down by adding longer waits.

## Context / Memory Issues

### "Exceeds dimension limit for many-image requests"
Too many screenshots accumulated in the conversation. Run `/compact` in Claude Code. The agent is configured to do this every 8-10 actions, but if it forgets, do it manually.

### Agent lost context after /compact
After compacting, the agent re-reads its knowledge base and session log to recover state. If it seems confused, tell it: "Re-read your knowledge base and today's session log."

## Testing Issues

### App crashed during testing
The agent will screenshot the crash and document it as a Critical bug. It will then try to reopen the app and continue testing.

### Agent is stuck / repeating actions
Tell it: "Stop. Take a screenshot and tell me what you see." This resets its understanding of the current screen state.

### Agent is testing the wrong app
Check `qa-agent/PRODUCT-KNOWLEDGE.md` and make sure your app's package name and URLs are correct.

## scrcpy Issues

### "Could not open video stream"
Try lowering the bitrate: `scrcpy --video-bit-rate 2M --max-size 800`

### Can't connect wirelessly
1. First connect via USB: `adb tcpip 5555`
2. Unplug USB
3. Connect: `adb connect YOUR_PHONE_IP:5555`
4. If it fails, check both devices are on the same WiFi network

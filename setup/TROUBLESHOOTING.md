# Troubleshooting

## Phone Connection Issues

### "Device not found" or "disconnected"
1. Open the Droidrun Portal app on your phone and check it shows "Connected"
2. Make sure the phone is plugged in and the screen is on
3. Wait 15 seconds, then retry the device check
4. If still disconnected, close and reopen the Droidrun Portal app

### Phone screen went dark / locked
The MobileRun API cannot press the power button. You need to:
1. Physically wake the phone up
2. Make sure "Stay awake" is enabled in Developer Options
3. Make sure the phone is plugged in (Stay awake only works while charging)

### Rate limit errors
The MobileRun API has rate limits. The agent automatically:
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

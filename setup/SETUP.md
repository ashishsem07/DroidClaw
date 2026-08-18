# Setup Guide

## What You Need

- An Android phone (Android 10+, any brand)
- USB cable (for initial setup; Wi-Fi works after that)
- A computer with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- `adb` (Android platform tools): `brew install android-platform-tools` on macOS, or your platform's equivalent

No accounts, no API keys. The phone control layer is the bundled local bridge (`local-bridge/`).

## Step 1: Prepare Your Phone

### Enable Developer Options + USB Debugging
1. Go to **Settings > About Phone**
2. Tap **Build Number** 7 times (you'll see a countdown toast)
3. Go back to **Settings > System > Developer Options**
4. Toggle **USB debugging** ON

### Prevent Phone From Sleeping
The bridge's REST surface has no POWER/WAKEUP endpoint, so if the phone sleeps mid-run the agent stops. (Escape hatch if it happens: `adb shell input keyevent KEYCODE_WAKEUP`.)

1. **Keep the phone plugged in** (charging cable)
2. **Developer Options > "Stay awake"** toggle ON (keeps screen on while charging)
3. **Settings > Display > Screen timeout** set to maximum (30 min)

With these settings, the phone stays awake indefinitely while plugged in.

## Step 2: Connect the Phone

```bash
# Plug in via USB, accept the "Allow USB debugging" prompt on the phone, then:
adb devices
```

The phone should be listed as `device` (not `unauthorized` or `offline`).

Optional, to go cordless on the same Wi-Fi (once per phone reboot):

```bash
adb tcpip 5555 && adb connect YOUR_PHONE_IP:5555
```

Find your phone's IP: **Settings > WiFi > tap your network > IP address**

If multiple devices are attached (e.g. emulators), pin the target: `export ADB_SERIAL=<serial>` (serials from `adb devices`).

## Step 3: Start the Local Bridge

```bash
local-bridge/start-bridge.sh
```

This starts a local REST server on `http://localhost:8723/v1` that drives the phone over ADB. Leave it running while the agent works. `qa-agent/RUN.md` already points at it; there is nothing to configure.

## Step 4: Install Your App

Install the app you want to test on the phone:
- From the Play Store, or
- Via `adb install your-app.apk`

Then update `qa-agent/PRODUCT-KNOWLEDGE.md` with:
- Your app's name and package ID
- Key features to test
- URLs (if it's a web app)
- Competitors to compare against

## Step 5: Sanity Check

Open Claude Code in the repo directory and run:

```
"Take a screenshot of the phone"
```

If you see your phone's screen, you're ready. Say **"Run the QA agent"** to start.

## Step 6 (Optional): Watch Live with scrcpy

If you want to watch what the agent is doing in real-time:

```bash
scrcpy --video-bit-rate 4M --max-size 1200
```

This is optional. The agent works fine without it, but it's nice to watch.

## Appendix: Legacy MobileRun Cloud Setup

Earlier versions of this repo ran on the MobileRun cloud API (an account, an API key, and the Droidrun Portal app on the phone). The local bridge replaces all of that with the same REST surface, so the cloud path is no longer needed. If you have an existing MobileRun-style setup and want to use it anyway, point the commands in `qa-agent/RUN.md` at your cloud base URL and put your real key in the Authorization headers; everything else is unchanged.

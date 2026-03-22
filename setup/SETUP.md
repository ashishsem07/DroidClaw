# Setup Guide

## What You Need

- An Android phone (Android 10+, any brand)
- USB cable (for initial setup)
- WiFi network (phone and computer on the same network)
- A computer with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
- A [MobileRun](https://mobilerun.ai) account

## Step 1: Prepare Your Phone

### Enable Developer Options
1. Go to **Settings > About Phone**
2. Tap **Build Number** 7 times (you'll see a countdown toast)
3. Go back to **Settings > System > Developer Options**

### Prevent Phone From Sleeping
The MobileRun API cannot send hardware keys (POWER/WAKEUP), so if the phone sleeps, the agent stops.

1. **Keep the phone plugged in** (charging cable)
2. **Developer Options > "Stay awake"** toggle ON (keeps screen on while charging)
3. **Settings > Display > Screen timeout** set to maximum (30 min)
4. **Settings > Battery > Battery optimization** set Droidrun Portal to "Unrestricted"

With these settings, the phone stays awake indefinitely while plugged in.

## Step 2: Install MobileRun Skill + Droidrun Portal

Droidrun Portal is **not on the Play Store**. You need to install it via the MobileRun SDK or the skill page.

### Option A: Via Skills Marketplace (recommended)
1. Go to [https://skillsmp.com/skills/droidrun-skills-mobilerun-skill-md](https://skillsmp.com/skills/droidrun-skills-mobilerun-skill-md)
2. Follow the instructions to install the MobileRun skill and Droidrun Portal APK on your phone
3. Open the Portal app on your phone and sign in
4. Note the **Device ID** shown on screen

### Option B: Via MobileRun SDK
1. Go to [mobilerun.ai](https://mobilerun.ai) and create an account
2. Follow their SDK documentation to download and install the Droidrun Portal APK on your phone
3. Open the Portal app on your phone and sign in
4. Note the **Device ID** shown on screen

## Step 3: Get Your API Key

1. Go to [mobilerun.ai](https://mobilerun.ai) and sign in
2. Navigate to your account/API settings
3. Copy your **API key** (starts with `dr_sk_...`)

## Step 4: Configure the Agent

Open `qa-agent/RUN.md` and replace the placeholder values:

```
API key: YOUR_API_KEY_HERE
Device ID: YOUR_DEVICE_ID_HERE
```

The RUN.md file has all the curl commands pre-built. Just replace these two values and everything works.

## Step 5: Install Your App

Install the app you want to test on the phone:
- From the Play Store, or
- Via `adb install your-app.apk`

Then update `qa-agent/PRODUCT-KNOWLEDGE.md` with:
- Your app's name and package ID
- Key features to test
- URLs (if it's a web app)
- Competitors to compare against

## Step 6: Sanity Check

Open Claude Code in the repo directory and run:

```
"Take a screenshot of the phone"
```

If you see your phone's screen, you're ready. Say **"Run the QA agent"** to start.

## Step 7 (Optional): WiFi ADB for scrcpy

If you want to watch what the agent is doing in real-time, set up scrcpy:

```bash
# Connect via USB first
adb tcpip 5555

# Then connect wirelessly (replace with your phone's IP)
adb connect YOUR_PHONE_IP:5555

# Launch scrcpy
scrcpy --video-bit-rate 4M --max-size 1200
```

Find your phone's IP: **Settings > WiFi > tap your network > IP address**

This is optional. The agent works fine without it, but it's nice to watch.

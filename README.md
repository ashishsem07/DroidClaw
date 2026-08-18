# Phone an AI Agent

**Give Claude a real phone. Let it test your app autonomously.**

No scripts. No Selenium. No test frameworks. No cloud service. Just an AI agent controlling a real Android phone over plain ADB: tapping buttons, typing messages, taking screenshots, and filing bug reports.

## What This Does

This repo contains a ready-to-use **autonomous QA agent** that:

- Opens your app on a real Android phone
- Tests features end-to-end (navigation, forms, chat, search, etc.)
- Finds bugs and UX issues across multiple flows
- Documents everything with screenshots and reproduction steps
- Maintains a knowledge base and compiles daily QA reports
- Compares your app against competitors

The agent runs on **Claude Code + a bundled local ADB bridge** (`local-bridge/`). No cloud relay, no API key, no subscription, no device slots. The phone sits on your desk doing its thing while you work on something else.

## Quick Start

### Prerequisites

- An Android phone (any recent model works)
- A [Claude Pro or Max](https://claude.ai/pricing) subscription (for Claude Code)
- `adb` installed (`brew install android-platform-tools` on macOS)
- ~15 minutes for initial setup

### Setup

1. Clone this repo
2. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code) if you haven't already
3. Follow the [Setup Guide](setup/SETUP.md): enable USB debugging, plug the phone in, start the bridge
4. Edit `qa-agent/PRODUCT-KNOWLEDGE.md` with your app's details
5. Open Claude Code in this directory and say: **"Run the QA agent"**

Claude will read the CLAUDE.md, load the agent configuration, connect to your phone, and start testing.

## How It Works

```
You: "Run the QA agent"
  |
  v
Claude reads CLAUDE.md -> loads agent config
  |
  v
Talks to the phone via the local ADB bridge (localhost REST)
  |
  v
Opens your app, starts testing features
  |
  v
Screenshots bugs, documents UX issues
  |
  v
Updates knowledge base, compiles daily report
```

The agent uses a structured memory system to track what it has tested, what bugs it has found, and what needs attention. Each session builds on the last.

### The local bridge

`local-bridge/adb-bridge.py` is a small dependency-free Python server that exposes a REST API on `http://localhost:8723/v1` (devices, screenshot, ui-state, tap, swipe, keyboard, global keys, app launch) and executes everything over plain ADB. It speaks the same v1 dialect as the MobileRun cloud API, so anything written against that API works unchanged by swapping the base URL. Start it with:

```bash
local-bridge/start-bridge.sh
```

## Repo Structure

```
CLAUDE.md                       <- Claude reads this automatically (the magic)
local-bridge/
  adb-bridge.py                 <- Local REST-over-ADB server (the phone control layer)
  start-bridge.sh               <- One-command bridge startup
setup/
  SETUP.md                      <- Phone + bridge setup guide
  TROUBLESHOOTING.md            <- Common issues and fixes
qa-agent/
  RUN.md                        <- Agent execution instructions
  PERSONA.md                    <- How the agent thinks and evaluates
  BEHAVIOR.md                   <- Testing protocols and frameworks
  PRODUCT-KNOWLEDGE.md          <- YOUR APP's details (edit this!)
  memory/
    knowledge-base.md           <- Feature health, known bugs, coverage
    bug-tracker.md              <- Full bug reports with repro steps
    ux-issues.md                <- UX issue reports
    growth-ideas.md             <- Growth opportunity tracking
    competitive-intel.md        <- Competitor comparisons
    weekly/                     <- Weekly digest archives
  session-logs/
    YYYY-MM-DD.md               <- Daily session action logs
  skills/                       <- Custom testing skills (extensible)
examples/
  sample-session-log.md         <- What a session log looks like
  sample-bug-report.md          <- What a bug report looks like
  sample-daily-report.md        <- What a daily report looks like
```

## Customizing for Your App

1. **Edit `qa-agent/PRODUCT-KNOWLEDGE.md`** with your app's features, URLs, and competitors
2. **Edit `qa-agent/BEHAVIOR.md`** to add feature-specific testing notes for your app
3. **Edit `qa-agent/PERSONA.md`** if you want to change how the agent evaluates (e.g., focus on accessibility, performance, etc.)

The agent is designed to be modular. Swap out the product knowledge and it works for any app.

## Beyond QA

The same setup can power other autonomous agents:

- **Competitor Research Agent** - Browse competitor apps, track feature changes, compare UX
- **UX Audit Agent** - Walk through user flows, count taps, time interactions, evaluate accessibility
- **Market Research Agent** - Browse the web, track pricing, compile intel reports
- **App Store Monitor** - Check competitor ratings, reviews, and updates

Each use case just needs a different set of instructions (RUN.md, PERSONA.md, BEHAVIOR.md). The phone control layer is the same.

## FAQ

**What phone do I need?**
Any Android phone running Android 10+. We used a OnePlus 10, but budget phones work fine too.

**Does it work with iOS?**
Not yet. The bridge drives Android via ADB and its accessibility tree; iOS has no equivalent open path.

**How much does it cost?**
Claude Pro ($20/month) or Max ($100/month). Nothing else - the bridge is local and free.

**Do I still need MobileRun?**
No. Earlier versions of this repo ran on the MobileRun cloud API. The bundled local bridge is a drop-in replacement for it (same REST endpoints), so there is no account, key, or per-device cost. If you do have a MobileRun-style cloud setup, the agent commands work against it unchanged by swapping the base URL back.

**Can it actually post/interact or just read?**
It has full control: tap, type, scroll, swipe, take screenshots. It can do anything you can do on the phone.

**Will it break my app?**
It tests like a real user. It won't root your phone or modify system settings. Worst case, it creates test accounts or sends test messages in your app.

## License

MIT

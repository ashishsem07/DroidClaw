# Phone an AI Agent

**Give Claude a real phone. Let it test your app autonomously.**

No scripts. No Selenium. No test frameworks. Just an AI agent controlling a real Android phone: tapping buttons, typing messages, taking screenshots, and filing bug reports.

## What This Does

This repo contains a ready-to-use **autonomous QA agent** that:

- Opens your app on a real Android phone
- Tests features end-to-end (navigation, forms, chat, search, etc.)
- Finds bugs and UX issues across multiple flows
- Documents everything with screenshots and reproduction steps
- Maintains a knowledge base and compiles daily QA reports
- Compares your app against competitors

The agent runs on **Claude Code + MobileRun API**. The phone sits on your desk doing its thing while you work on something else.

## Quick Start

### Prerequisites

- An Android phone (any recent model works)
- A [Claude Pro or Max](https://claude.ai/pricing) subscription (for Claude Code)
- A [MobileRun](https://mobilerun.ai) account and API key
- ~30 minutes for initial setup

### Setup

1. Clone this repo
2. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code) if you haven't already
3. Follow the [Setup Guide](setup/SETUP.md) to connect your phone
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
Connects to phone via MobileRun API
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

## Repo Structure

```
CLAUDE.md                       <- Claude reads this automatically (the magic)
setup/
  SETUP.md                      <- Phone + MobileRun setup guide
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
Not yet. MobileRun currently supports Android only.

**How much does it cost?**
Claude Pro ($20/month) or Max ($100/month) + MobileRun API costs. No other infrastructure needed.

**Can it actually post/interact or just read?**
It has full control: tap, type, scroll, swipe, take screenshots. It can do anything you can do on the phone.

**Will it break my app?**
It tests like a real user. It won't root your phone or modify system settings. Worst case, it creates test accounts or sends test messages in your app.

## License

MIT

# Phone an AI Agent

## What This Is
An autonomous QA agent that tests mobile apps on a real Android phone, using Claude Code + a local ADB bridge (`local-bridge/adb-bridge.py`, REST on `http://localhost:8723/v1`).

## Quick Start
When the user says "run the QA agent" or similar:
1. Read `qa-agent/RUN.md` and follow all steps
2. The RUN.md will tell you to load PERSONA.md, BEHAVIOR.md, PRODUCT-KNOWLEDGE.md, and memory files
3. Make sure the local bridge is running (`local-bridge/start-bridge.sh`); connect to the phone through it
4. Start testing

## First Time Setup
If the user hasn't set up their phone yet, guide them through `setup/SETUP.md`:
1. Help them install `adb` and enable USB debugging on the phone
2. Plug the phone in (or `adb connect` over Wi-Fi) and verify `adb devices` shows it
3. Start the bridge: `local-bridge/start-bridge.sh`
4. Run a sanity check (screenshot the home screen via the bridge)
5. Have them edit `qa-agent/PRODUCT-KNOWLEDGE.md` with their app's details

## File Structure
```
local-bridge/
  adb-bridge.py           <- Local REST-over-ADB server (the phone control layer)
  start-bridge.sh         <- One-command bridge startup
qa-agent/
  RUN.md                  <- START HERE: Main execution file
  PERSONA.md              <- How the agent thinks and evaluates
  BEHAVIOR.md             <- Testing protocols and frameworks
  PRODUCT-KNOWLEDGE.md    <- App details, features, competitors (USER EDITS THIS)
  memory/
    knowledge-base.md     <- Working memory: feature health, bugs, coverage
    bug-tracker.md        <- Full bug reports with repro steps
    ux-issues.md          <- UX issue reports
    growth-ideas.md       <- Growth opportunity tracking
    competitive-intel.md  <- Competitor tracking
    weekly/               <- Weekly digest archives
  session-logs/           <- Daily session action logs
  skills/                 <- Custom testing skills (extensible)
```

## Key Rules
- ALWAYS screenshot bugs and UX issues (visual evidence is mandatory)
- ALWAYS include exact reproduction steps for bugs
- ALWAYS update the knowledge base at session end
- ALWAYS compile a daily report at end of each session day
- Run `/compact` every 8-10 phone actions to prevent context overflow from screenshots

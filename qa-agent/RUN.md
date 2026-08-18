# QA & Growth Agent — Run This File

When Claude reads this file, immediately start the Mobile QA & Growth agent. Read all referenced files first, then begin operating.

---

## Step 0 — Load Context

Before starting, read these files in this order:
1. `qa-agent/PERSONA.md` — Identity, role, evaluation approach
2. `qa-agent/BEHAVIOR.md` — Testing protocols, report formats, prioritization rules
3. `qa-agent/PRODUCT-KNOWLEDGE.md` — Your app's platform knowledge, competitors
4. `qa-agent/memory/knowledge-base.md` — Working memory: feature health, known bugs, active issues
5. `qa-agent/session-logs/` — Check the latest session log for recent activity

Read ALL of these before doing anything on the phone.

---

## Step 0.5 — Phone Sleep Prevention (One-Time Setup)

The bridge's REST surface has no POWER/WAKEUP endpoint, so if the phone sleeps mid-run the agent stops. (Local escape hatch: `adb shell input keyevent KEYCODE_WAKEUP`.) **The phone must be configured to never sleep:**

1. **Keep the phone plugged in** (charging cable)
2. **Developer Options > "Stay awake"** — toggle ON (keeps screen on while charging)
   - To enable Developer Options: Settings > About Phone > tap "Build number" 7 times
3. **Settings > Display > Screen timeout** — set to maximum (30 min)
4. **Settings > Battery > Battery optimization** — set Droidrun Portal to "Unrestricted"

If all of these are set, the phone will stay awake indefinitely while plugged in.

---

## Step 1 — Connect to Phone

Base URL: `http://localhost:8723/v1` (the local ADB bridge; start it once per session with `local-bridge/start-bridge.sh`)
Device ID: `local`
Auth header: not required. The local bridge ignores it; the header stays in the commands below only so they also work unchanged against a legacy MobileRun cloud account (swap the base URL and use your real key).

Check device is ready:
```bash
curl -s "http://localhost:8723/v1/devices" \
  -H "Authorization: Bearer local"
```
If state is "ready", proceed. If disconnected:
1. Ask user to open the Droidrun Portal app on the phone and ensure the phone is plugged in
2. Wait 15 seconds, then re-check device state
3. Retry up to 3 times with 15-second waits before giving up

## Step 2 — Open Your App

### For Web Apps (Chrome)
```bash
curl -s -X PUT "http://localhost:8723/v1/devices/local/apps/com.android.chrome" \
  -H "Authorization: Bearer local" \
  -H "Content-Type: application/json" \
  -d '{}'
```
Then navigate to your app's URL.

### For Native Apps
```bash
curl -s -X PUT "http://localhost:8723/v1/devices/local/apps/YOUR_APP_PACKAGE_HERE" \
  -H "Authorization: Bearer local" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Take a screenshot to verify the app is open.

---

## Phone Control Reference

### Rate Limit Handling
The local bridge has no rate limits, so no `sleep` is needed between calls. If you point these commands at the legacy MobileRun cloud API instead, add `sleep 2` between consecutive calls and use this retry wrapper:

```bash
# Rate-limit-aware API call wrapper (paste once per session)
mobilerun() {
  local retries=0
  while [ $retries -lt 3 ]; do
    local response
    response=$(curl -s -w "\n%{http_code}" "$@")
    local http_code=$(echo "$response" | tail -1)
    local body=$(echo "$response" | sed '$d')
    if echo "$body" | grep -q "Rate limit"; then
      retries=$((retries + 1))
      echo "Rate limited, waiting 10s (retry $retries/3)..." >&2
      sleep 10
    else
      echo "$body"
      return 0
    fi
  done
  echo "$body"
  return 1
}
```

(Cloud only. On the local bridge, plain `curl -s` is fine.)

```bash
# Screenshot (auto-resize to stay under 2000px limit)
curl -s "http://localhost:8723/v1/devices/local/screenshot" \
  -H "Authorization: Bearer local" \
  -o /tmp/qa_screen_raw.png && \
  sips --resampleHeight 1600 /tmp/qa_screen_raw.png --out /tmp/qa_screen.png 2>/dev/null && \
  rm -f /tmp/qa_screen_raw.png

# UI tree (get tap coordinates)
curl -s "http://localhost:8723/v1/devices/local/ui-state?filter=true" \
  -H "Authorization: Bearer local"

# Tap
curl -s -X POST "http://localhost:8723/v1/devices/local/tap" \
  -H "Authorization: Bearer local" \
  -H "Content-Type: application/json" \
  -d '{"x": X, "y": Y}'

# Long press
curl -s -X POST "http://localhost:8723/v1/devices/local/swipe" \
  -H "Authorization: Bearer local" \
  -H "Content-Type: application/json" \
  -d '{"startX": X, "startY": Y, "endX": X, "endY": Y, "duration": 1000}'

# Type text
curl -s -X POST "http://localhost:8723/v1/devices/local/keyboard" \
  -H "Authorization: Bearer local" \
  -H "Content-Type: application/json" \
  -d '{"text": "message here", "clear": false}'

# Back button
curl -s -X POST "http://localhost:8723/v1/devices/local/global" \
  -H "Authorization: Bearer local" \
  -H "Content-Type: application/json" \
  -d '{"action": 1}'

# Home button
curl -s -X POST "http://localhost:8723/v1/devices/local/global" \
  -H "Authorization: Bearer local" \
  -H "Content-Type: application/json" \
  -d '{"action": 2}'

# Scroll down
curl -s -X POST "http://localhost:8723/v1/devices/local/swipe" \
  -H "Authorization: Bearer local" \
  -H "Content-Type: application/json" \
  -d '{"startX": 540, "startY": 1500, "endX": 540, "endY": 400, "duration": 300}'

# Scroll up
curl -s -X POST "http://localhost:8723/v1/devices/local/swipe" \
  -H "Authorization: Bearer local" \
  -H "Content-Type: application/json" \
  -d '{"startX": 540, "startY": 400, "endX": 540, "endY": 1500, "duration": 300}'
```

### Extract UI elements helper:
```bash
... | python3 -c "
import json,sys; data=json.load(sys.stdin)
def ex(n,r=[]):
    t=n.get('text','').strip(); d=n.get('contentDescription','').strip()
    b=n.get('boundsInScreen',{}); cx=(b.get('left',0)+b.get('right',0))//2; cy=(b.get('top',0)+b.get('bottom',0))//2
    l=t or d
    if l: r.append({'l':l,'cx':cx,'cy':cy,'click':n.get('isClickable',False)})
    [ex(c,r) for c in n.get('children',[])]
    return r
[print(f\"({'TAP' if e['click'] else '   '}) ({e['cx']:4},{e['cy']:4}) {e['l'][:80]}\") for e in ex(data['a11y_tree'])]
"
```

---

## Context Management (Prevent Image Overflow)

Screenshots accumulate in the conversation context. To avoid the "exceeds dimension limit for many-image requests" error:

- **Run `/compact` every 8-10 phone actions** (screenshots, UI state reads, taps, etc.)
- If you notice the conversation getting long, compact proactively
- After compacting, re-read any critical state you need from your session log or by taking a fresh screenshot

---

## Session Types

### Type A: Feature Testing Session (primary)
**Goal:** Systematically test your app's features on mobile and web.

Rotate through features across sessions. Test 3-5 features per session. Check `qa-agent/PRODUCT-KNOWLEDGE.md` for the feature list and test matrix.

### Type B: Competitor Research Session
**Goal:** Use competitor apps and compare features, UX, and engagement hooks.

Spend 15-20 minutes per competitor app. Compare the same features you test on your app.

### Type C: UX Deep Dive Session
**Goal:** Walk through specific user flows and evaluate them critically.

For every flow, evaluate: first impression, friction points, loading states, error handling, empty states, navigation, visual consistency, accessibility.

### Type D: Mixed Session (recommended daily)
1. Feature testing (30 min) - test 3-5 features
2. Competitor check (20 min) - check 1-2 competitor apps
3. UX evaluation (10 min) - deep dive on one flow
4. Growth brainstorm (10 min) - document ideas based on findings
5. Compile daily report

Default to Type D.

---

## Agent Loop

Run this loop continuously:

1. **Check knowledge-base.md** - review known bugs, feature health, last session findings
2. **Open your app** (native or web, based on what needs testing)
3. **Test features:**
   - Work through the test matrix for today's rotation
   - Screenshot EVERY bug or UX issue found
   - Document reproduction steps as you go
4. **Check competitor apps** (if doing Type B or D):
   - Open 1-2 competitor apps
   - Compare the same feature you just tested on your app
   - Note differences
5. **Evaluate UX:**
   - Walk through specific user flows
   - Note friction, confusion, delight
   - Screenshot everything
6. **Brainstorm growth ideas** based on testing and competitor research
7. **Log every action** to session log
8. **Keepalive:** During any idle wait longer than 60 seconds, take a screenshot mid-wait to keep the phone awake and verify the device is still connected. If disconnected:
   - Log the disconnection in the session log
   - Ask the user to check the phone (ensure it's plugged in, Portal is open)
   - Retry device check every 15 seconds, up to 3 times
   - If it comes back, resume. If not, end session gracefully (save all memory/logs first)
9. **Repeat**
10. **At session end:** compile daily report, update knowledge base, update bug tracker and competitive intel

---

## Session Logging

**File:** `qa-agent/session-logs/YYYY-MM-DD.md`

One file per day. Each session gets its own section.

### What to log (as a markdown table per session):
| Field | Description |
|-------|-------------|
| Time | Approximate timestamp |
| Platform | Your app (native/web) / competitor name |
| Feature | What feature or flow was tested |
| Action | tested, found bug, UX issue, compared, researched |
| Result | OK / Bug / UX Issue / Idea |
| Notes | Brief description of finding |

Also log:
- **Features tested with no issues** (so we know what was checked)
- **Competitor observations** (brief, details go in competitive-intel.md)
- **Technical issues** encountered with the phone or testing

---

## Memory System

Three tiers. Read Tier 1 at session start. Write to all tiers at session end.

### Tier 1: Knowledge Base (read every session)
**File:** `qa-agent/memory/knowledge-base.md`

Structured, curated, constantly updated. Contains:
- **Feature health dashboard**: status of every core feature (OK / Known Issue / Broken)
- **Active bugs**: top bugs by severity with brief descriptions
- **Active UX issues**: top UX issues by severity
- **Recent changes**: any new features or fixes noticed
- **Testing coverage**: which features were last tested and when
- **Growth ideas pipeline**: top ideas by effort/impact

**Rules:** Summarize, don't append. Replace stale info. Keep under 200 lines.

### Tier 2: Specialized Files (read as needed)
- `qa-agent/memory/bug-tracker.md` - Full bug reports with repro steps
- `qa-agent/memory/ux-issues.md` - Full UX issue reports
- `qa-agent/memory/growth-ideas.md` - Full growth idea write-ups
- `qa-agent/memory/competitive-intel.md` - Competitor tracking and comparisons

### Tier 3: Weekly Digests (long-term memory)
**Directory:** `qa-agent/memory/weekly/YYYY-WXX.md`

Compress session logs at end of week into:
- Bugs found and their current status (fixed, open, wontfix)
- UX improvements suggested and status
- Competitive landscape changes
- Growth ideas proposed and status
- Feature health trends (improving, degrading, stable)

### Session End Checklist
After every session, before stopping:
1. Ensure today's session log is complete
2. Update knowledge-base.md: feature health, active bugs, testing coverage
3. Write full bug/UX/growth reports to Tier 2 files if new findings
4. Update competitive-intel.md with any new competitor observations
5. If it's end of week: create weekly digest, trim old session logs

---

## Report Formats

### Bug Report
```
## Bug: [Short descriptive title]

**Severity:** Critical / High / Medium / Low
**Platform:** Android App / Mobile Web / Desktop Web
**Device:** [Your device model], Android [version]
**Date:** [YYYY-MM-DD]

### Steps to Reproduce
1. [Exact step]
2. [Exact step]
3. [Exact step]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Screenshots
[Reference screenshot filenames saved during session]

### Additional Context
[Network conditions, account state, etc.]
```

### UX Issue Report
```
## UX Issue: [Short descriptive title]

**Screen/Flow:** [Which screen or user flow]
**Platform:** Android App / Mobile Web / Desktop Web
**Severity:** Blocker / Major / Minor / Cosmetic
**Date:** [YYYY-MM-DD]

### What Happens
[Describe the current experience]

### Why It's a Problem
[Who is affected, what's the impact on engagement/conversion/retention]

### Suggested Improvement
[Concrete recommendation]

### Competitor Reference
[If a competitor handles this better, describe how]
```

### Growth Idea Format
```
## Growth Idea: [Short title]

**Category:** Conversion / Retention / Engagement / Acquisition
**Effort:** Low / Medium / High
**Expected Impact:** Low / Medium / High
**Spotted on:** [Competitor name or own testing]
**Date:** [YYYY-MM-DD]

### Observation
[What you noticed]

### Hypothesis
[If we do X, we expect Y because Z]

### Suggested Test
[How to validate before fully building]
```

### Daily Report Structure
```
# Daily QA & Growth Report — [YYYY-MM-DD]

## Summary
[2-3 sentence overview]

## Bugs Found
[List with severity]

## UX Issues
[List with severity]

## Competitive Updates
[Any new features or changes spotted]

## Growth Opportunities
[Top 3 ideas from today]

## Feature Health Check
| Feature | Status | Notes |
|---------|--------|-------|
| [Feature 1] | OK / Issue | [brief note] |
| [Feature 2] | OK / Issue | [brief note] |

## Priority Actions
1. [Most urgent]
2. [Second priority]
3. [Third priority]
```

---

## Principles

1. **Test like a real user.** Don't just verify features work. Use the app the way your target user would.
2. **Reproduce before reporting.** Every bug must have clear repro steps. If you can't reproduce it, note that.
3. **Compare, don't just test.** Always benchmark against what competitors are doing.
4. **Prioritize ruthlessly.** Not every bug or idea is worth acting on. Flag severity and impact.
5. **Screenshots are mandatory.** Every bug and UX issue needs visual evidence.
6. **Think in metrics.** Tie every observation back to a product metric: retention, conversion, engagement, or acquisition.

---

## Key Rules (Never Break These)

- ALWAYS screenshot bugs and UX issues (visual evidence is mandatory)
- ALWAYS include exact reproduction steps for bugs
- ALWAYS compare your app against competitors when evaluating features
- ALWAYS update the knowledge base at session end
- ALWAYS compile a daily report at end of each session day
- NEVER skip the feature health check
- NEVER report a bug you cannot reproduce (mark it as "intermittent" with context)
- NEVER assume a feature works without testing it on the actual phone
- Prioritize by severity and user impact, not by how interesting the bug is

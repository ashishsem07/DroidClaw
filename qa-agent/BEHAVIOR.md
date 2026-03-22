# Behavior Rules — QA & Growth Agent

## Testing Protocols

### Feature Testing Protocol
For every feature you test, follow this sequence:

1. **Baseline check** — Does the feature load and appear functional?
2. **Happy path** — Complete the main use case successfully
3. **Edge cases** — Try unusual inputs, rapid interactions, boundary conditions
4. **Error states** — Force errors (bad input, empty fields, network issues)
5. **Cross-reference** — Check the same feature on the other platform (web vs mobile)
6. **Screenshot** — Capture current state for the record
7. **Log** — Record result in session log

### Competitor Testing Protocol
When testing a competitor app:

1. **Install/open** — Note the first impression, onboarding experience
2. **Match test** — Test the same feature you tested on your app
3. **Note differences** — What's better? What's worse? What's different?
4. **Look for new features** — Anything your app doesn't have?
5. **Check monetization** — What's free? What's paywalled? Pricing?
6. **Screenshot** — Capture anything notable
7. **Log** — Record findings in session log, detailed write-up in competitive-intel.md

### UX Evaluation Protocol
When evaluating a user flow:

1. **Set a goal** — "I want to [user goal]"
2. **Navigate naturally** — Don't use shortcuts you know. Go through the UI as a user would.
3. **Count taps** — How many taps to complete the goal?
4. **Note confusion** — Any moment you pause or aren't sure what to tap
5. **Check feedback** — Does the app tell you what happened? Success states? Error states?
6. **Time it** — How long did the full flow take?
7. **Compare** — How many taps and how long does the same flow take on a competitor?

---

## Growth Analysis Framework

### When Spotting Growth Opportunities

Think in terms of these levers:

**Acquisition** — How do new users find the app?
- App store optimization (ASO)
- SEO for web pages
- Viral loops (sharing content, inviting friends)
- Referral mechanics

**Activation** — Do new users have a great first experience?
- Time to first value (should be under 60 seconds)
- Onboarding quality
- Default content quality
- First impression of core feature

**Retention** — Do users come back?
- Push notification strategy
- Streaks, daily rewards, gamification
- Progress and relationship building
- Content freshness

**Revenue** — Do users pay?
- Free tier generosity vs paywall placement
- Premium feature desirability
- Pricing competitiveness vs competitors
- Upsell moments and triggers

**Referral** — Do users invite others?
- Share mechanics
- Social proof
- Community features

### When Comparing to Competitors

Always ask:
1. "Would our user switch to this competitor? Why?"
2. "Would a competitor user switch to us? Why not?"
3. "What's the #1 thing this competitor does better?"
4. "What's the #1 thing our app does better?"

---

## Reporting Priorities

### Always Report Immediately (Critical/High)
- App crashes
- Data loss
- Security issues
- Core features completely broken
- Payment/billing issues

### Report in Daily Summary (Medium)
- Non-core features broken
- Significant UX friction
- Performance issues (slow loads, high battery)
- Competitor launches that are threatening

### Batch in Weekly Digest (Low)
- Cosmetic issues
- Minor UX improvements
- Nice-to-have feature ideas
- General competitive observations

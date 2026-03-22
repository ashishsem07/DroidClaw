# Sample Bug Report

## Bug: Ad overlay intercepts back button in chat view

**Severity:** High
**Platform:** Mobile Web
**Device:** OnePlus 10, Android 14
**Date:** 2026-03-15

### Steps to Reproduce
1. Open the app in Chrome on mobile
2. Navigate to Explore and search for any character
3. Tap a character to open chat
4. Send a few messages
5. Try to tap the back arrow (top-left) to return to explore

### Expected Behavior
Tapping the back arrow navigates back to the explore/search results page.

### Actual Behavior
An ad overlay (SafeFrame ad unit) is positioned on top of the back button. Tapping the back arrow clicks the ad instead, opening the Play Store or an external link. The user is trapped in the chat view with no obvious way to navigate back.

### Screenshots
- `qa_screen_bug_ad_overlay.png` — Shows the ad overlay covering the back button area

### Additional Context
- The bottom navigation bar is not visible in the chat view, so there's no alternative navigation
- Android's system back button works but can exit the app entirely
- This affects all chat views, not just specific characters
- Impact: Users who can't navigate back will likely close the app entirely (churn risk)

### Workaround
Use the Android system back gesture/button instead of the in-app back arrow.

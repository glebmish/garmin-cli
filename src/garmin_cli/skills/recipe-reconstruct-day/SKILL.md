---
name: recipe-reconstruct-day
description: Use when reconstructing what someone physically did during a day or a specific time window from Garmin data — combines activities, step buckets, and sleep into a timeline.
---

# recipe-reconstruct-day

Goal: answer "what was happening at HH:MM?" or "reconstruct this day" from Garmin
data. No single endpoint does this — combine three.

## Steps

1. **Bound the day with sleep.** Sleep keys on the WAKE date.

   ```bash
   garmin sleep get --date 2026-05-11 \
     --fields sleepStartTimestampGMT,sleepEndTimestampGMT,sleepWindowConfirmed
   ```

   `sleepEndTimestampGMT` (epoch ms, UTC) ≈ when the day's activity begins.

2. **List discrete auto-detected activities** for the day.

   ```bash
   garmin activities list --date 2026-05-11 \
     --fields startTimeLocal,duration,distance,activityType,activityName
   ```

   These are the high-confidence "known" blocks (a run, a ride). `duration` is
   seconds, `distance` meters, `startTimeLocal` is local wall-clock.

3. **Fill the gaps with step buckets.** For windows with no auto-detected
   activity, pull steps and look for sustained movement.

   ```bash
   garmin steps get --date 2026-05-11 --bucket 30m
   ```

   A run of buckets with `primaryActivityLevel` `active`/`highlyActive` and
   non-trivial `steps` = movement the watch didn't classify as an activity
   (a walk, errands). `sedentary`/`none` = at rest.

## Stitching notes

- **Unit/zone mismatch is the trap.** `startTimeGMT` and step `startGMT`/`endGMT`
  are UTC; `startTimeLocal` is local. Convert everything to one zone before
  aligning. Sleep timestamps are epoch **milliseconds**.
- **Activities take precedence over step inference** where they overlap — they're
  the higher-confidence signal.
- **Missing pieces are normal:** no confirmed sleep → `sleep get` exits 1; no
  activities → empty array (exit 0). Degrade gracefully to step buckets alone.

## Answering a point-in-time question

For "was 09:00–09:30 a walk?": check step buckets overlapping that window
(convert 09:00 local → UTC first), then confirm against `activities list --type
walking` for the day.

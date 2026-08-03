# Variable Difficulty (VarDiff)

**Document:** 08-VARIABLE-DIFFICULTY.md

**Version:** 1.0 (Development)

---

# Purpose

Variable Difficulty (VarDiff) automatically adjusts the mining difficulty assigned to each worker so that miners submit shares at a consistent target interval.

Instead of every miner using the same share difficulty, Seymour continuously tunes each worker independently based on its actual hashrate.

This allows a small USB miner and a large ASIC farm to operate efficiently on the same pool.

---

# Why Variable Difficulty Exists

Without VarDiff:

- Slow miners submit very few shares.
- Fast miners flood the server with millions of low-value shares.
- Database growth becomes excessive.
- Network traffic increases dramatically.
- Statistics become noisy.

Variable Difficulty solves these problems by normalizing the share rate across all miners.

---

# Design Goals

The Seymour VarDiff engine is designed to:

- Maintain a consistent share interval
- Reduce unnecessary network traffic
- Reduce database writes
- Improve hashrate estimation
- Scale from hobby miners to industrial farms
- Operate independently for every connected worker

---

# Target Share Interval

Every worker attempts to submit one accepted share approximately every configured interval.

Example:

```
15 seconds
```

If shares arrive too quickly:

```
Difficulty Increases
```

If shares arrive too slowly:

```
Difficulty Decreases
```

---

# Independent Worker Control

Each worker maintains its own difficulty.

Example:

```
Worker 001

Difficulty

10752

-------------------

Worker 002

Difficulty

5376

-------------------

Worker 003

Difficulty

84
```

Difficulty is never shared between workers.

---

# Startup Difficulty

New workers begin at the configured minimum difficulty.

Example:

```
42
```

This allows immediate mining while Seymour measures actual worker performance.

---

# Difficulty Progression

As shares are received, difficulty increases.

Typical progression:

```
42

↓

84

↓

168

↓

336

↓

672

↓

1344

↓

2688

↓

5376

↓

10752
```

The progression is adaptive rather than fixed.

---

# Retarget Algorithm

After every accepted share Seymour evaluates:

```
Observed Share Interval

↓

Target Share Interval

↓

Adjustment Required?

↓

Yes

↓

Issue New Difficulty
```

Retarget decisions are based on actual mining performance rather than estimated hashrate.

---

# Retarget Event

A difficulty change records:

- Previous difficulty
- New difficulty
- Observed share interval
- Target share interval
- Timestamp
- Worker

These events are stored permanently.

---

# Difficulty History

Difficulty changes are recorded in:

```
stratum_difficulty_history
```

Typical record:

```
Worker

Old Difficulty

New Difficulty

Observed Seconds

Target Seconds

Reason
```

This provides a complete history of worker performance.

---

# Job Synchronization

Changing difficulty alone is insufficient.

Bitcoin miners continue submitting shares against previously issued jobs.

To maintain protocol correctness Seymour performs two operations together.

```
Difficulty Change

↓

mining.set_difficulty

↓

Generate New Job

↓

mining.notify
```

The miner immediately begins working on a job matching the new difficulty.

---

# Session-Based Job Tracking

Every issued job stores the difficulty that was active when it was created.

Conceptually:

```
Session

↓

Job ID

↓

Assigned Difficulty
```

This mapping remains available until the job expires.

---

# Share Validation

When a share arrives:

```
Submitted Job

↓

Lookup Original Difficulty

↓

Validate Against Original Difficulty
```

Shares are never validated using the worker's current difficulty.

They are always validated using the difficulty assigned when the job was issued.

---

# Why This Matters

ASIC miners frequently submit shares generated from jobs issued before a difficulty change.

Without session-based job tracking:

```
Job Issued

↓

Difficulty Changes

↓

Share Arrives

↓

Validated Against Wrong Difficulty

↓

Rejected
```

This creates false "low difficulty share" errors.

---

# Session-Based Validation Fix

Seymour records:

```
Job A

↓

Difficulty 5376

---------------

Job B

↓

Difficulty 10752
```

If a miner submits a share for Job A after Job B exists:

```
Lookup Job A

↓

Difficulty 5376

↓

Correct Validation
```

The newer difficulty is ignored.

---

# Operational Impact

During development this enhancement eliminated nearly all false Variable Difficulty rejections.

Before implementation:

```
Accepted

≈0.3%

Rejected

≈99.7%
```

After implementation:

```
Accepted

100%

Rejected

0%
```

This confirmed that miners were producing valid work and that the rejection problem resulted from incorrect difficulty association during validation.

---

# Clean Jobs

Difficulty adjustments always generate clean jobs.

```
clean_jobs = true
```

This instructs miners to discard obsolete work and begin mining the new template immediately.

---

# Multiple Workers

Each worker retargets independently.

Example:

```
Worker 001

5376

---------------

Worker 002

10752

---------------

Worker 003

336
```

Fast miners do not affect slower miners.

---

# Database Persistence

Difficulty adjustments survive process restarts because historical changes are written to PostgreSQL.

Persistent history supports:

- Diagnostics
- Historical reporting
- Hashrate analysis
- Performance tuning

---

# Logging

Retarget events are logged.

Example:

```
VARDIFF_JOB

worker=...

old_difficulty=5376

new_difficulty=10752

job=...
```

These events simplify troubleshooting and performance analysis.

---

# Benefits

The Seymour Variable Difficulty engine provides:

- Lower bandwidth usage
- Lower database growth
- Better hashrate estimation
- Stable share intervals
- Independent worker tuning
- Accurate statistics
- Improved ASIC compatibility
- Correct historical job validation

---

# Relationship to Other Components

Variable Difficulty works closely with:

- Session Manager
- Stratum Dispatcher
- Job Engine
- Share Validator
- Native Statistics
- PostgreSQL

Together these components provide deterministic and protocol-compliant mining.

---

# Future Enhancements

Future versions may include:

- Adaptive target intervals
- Hardware-specific tuning
- Machine-learning difficulty prediction
- Multi-algorithm support
- Cluster-wide difficulty coordination

---

# Next Step

Continue with:

**09-DATABASE-SCHEMA.md**

# Variable Difficulty (VarDiff) Engine

**Document:** 34-VARDIFF-ENGINE.md

**Version:** 1.0 (Engineering Specification)

---

# Purpose

This document describes the internal design of the Seymour Pool Engine Variable Difficulty (VarDiff) subsystem.

VarDiff automatically adjusts worker difficulty to maintain consistent share submission intervals while ensuring accurate hashrate estimation and efficient pool operation.

---

# Design Goals

The VarDiff engine is designed to provide:

- Stable share submission rates
- Accurate hashrate estimation
- Low network overhead
- Fair worker evaluation
- Session isolation
- Deterministic validation

---

# Philosophy

Difficulty belongs to the **job**, not the worker.

When a worker's difficulty changes, previously issued jobs continue to validate using the difficulty that existed when those jobs were created.

This prevents valid shares from being rejected after a difficulty adjustment.

---

# Processing Flow

```
Worker Connects

↓

Initial Difficulty

↓

Mining Begins

↓

Observe Share Timing

↓

VarDiff Decision

↓

Difficulty Adjustment

↓

Issue New Job

↓

Continue Mining
```

---

# Initial Difficulty

Every new session begins with a configured starting difficulty.

Example:

```
42
```

This value should be appropriate for the expected class of mining hardware.

---

# Observation

The engine continuously measures:

- Share arrival rate
- Average submission interval
- Recent mining activity

Decisions are based on observed mining behavior rather than theoretical hashrate.

---

# Adjustment Strategy

If shares arrive too quickly:

```
Increase Difficulty
```

If shares arrive too slowly:

```
Decrease Difficulty
```

The goal is to maintain a consistent target submission interval.

---

# Session State

Each Stratum session maintains:

- Current difficulty
- Recently issued jobs
- Job-to-difficulty mapping
- Share counters
- Timing history

This state is isolated from all other workers.

---

# Job Association

When a new job is issued:

```
Job ID

↓

Assigned Difficulty

↓

Session Mapping
```

The session records:

```
job_id → assigned_difficulty
```

This mapping is retained for recently issued jobs.

---

# Validation

During share submission:

```
Submitted Job

↓

Lookup Job

↓

Lookup Assigned Difficulty

↓

Validate Share

↓

Accept / Reject
```

Validation never uses the worker's current difficulty if a historical job mapping exists.

---

# Difficulty History

Difficulty changes are persisted.

Typical fields include:

- Worker
- Previous difficulty
- New difficulty
- Timestamp
- Reason

This information supports diagnostics and historical analysis.

---

# Difficulty Scaling

Version 1.0 generally scales difficulty using multiplicative adjustments.

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
```

Future algorithms may support finer-grained scaling.

---

# Job Refresh

After every difficulty adjustment the server issues:

1. `mining.set_difficulty`
2. `mining.notify`

The newly generated job becomes the preferred mining job for the session.

Older jobs remain valid until naturally retired.

---

# Job Retirement

To prevent unbounded memory growth, only a limited number of recent job mappings are retained.

Example:

```
16 recent jobs
```

Older mappings are discarded automatically.

---

# Session Isolation

Difficulty adjustments affect only the worker that triggered them.

Changing one worker's difficulty must never alter another worker's mining state.

---

# Hashrate Estimation

Assigned difficulty contributes directly to hashrate estimation.

Using the correct historical difficulty ensures accurate statistics even during frequent VarDiff adjustments.

---

# Operational Logging

Important log events include:

```
VARDIFF_JOB

Difficulty Increase

Difficulty Decrease

Observation Interval

Assigned Difficulty
```

These events simplify production troubleshooting.

---

# Performance

VarDiff calculations should remain lightweight.

The algorithm executes continuously and must avoid introducing noticeable latency into the share validation pipeline.

---

# Failure Handling

If VarDiff encounters an unexpected error:

- Preserve the current difficulty.
- Continue mining.
- Record diagnostic information.
- Avoid disconnecting the worker unless necessary.

Mining availability always takes priority.

---

# Future Enhancements

Potential future improvements include:

- Hardware-aware tuning
- Adaptive target intervals
- Historical learning
- AI-assisted optimization
- Pool-wide balancing
- Dynamic configuration

These enhancements should preserve backward compatibility whenever practical.

---

# Engineering Principles

The VarDiff engine follows these principles:

- Difficulty belongs to the job.
- Jobs belong to the session.
- Validation uses the assigned job difficulty.
- Statistics derive from validated shares.
- Workers remain completely isolated.

These invariants should not be violated by future development.

---

# Summary

The Seymour VarDiff Engine maintains efficient share submission rates while preserving deterministic validation through session-specific job tracking and historical difficulty assignment.

This architecture enables accurate hashrate estimation, stable mining performance, and reliable production operation.

---

# Next Step

Continue with:

**35-SHARE-VALIDATION-ENGINE.md**

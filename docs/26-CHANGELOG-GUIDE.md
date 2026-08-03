# Changelog Guide

**Document:** 26-CHANGELOG-GUIDE.md

**Version:** 1.0 (Development)

---

# Purpose

This document defines how changes should be recorded throughout the Seymour Pool Engine project.

A well-maintained changelog allows developers, operators, and users to understand what changed between releases without examining Git history.

---

# Goals

The changelog should:

- Document significant changes.
- Record new features.
- Record bug fixes.
- Record database changes.
- Record API changes.
- Record breaking changes.
- Record documentation updates.

The changelog is intended for humans rather than machines.

---

# Format

Each release should include:

```
Version

Release Date

Summary

New Features

Improvements

Bug Fixes

Database

REST API

Documentation

Known Issues
```

---

# Example

```
## Version 1.0.0

Release Date:
2026-08-15

Summary

Initial production release of the Seymour Pool Engine.

### New Features

• Native Stratum Server
• Native Statistics Engine
• REST API
• Variable Difficulty
• Block Submission
• PostgreSQL Storage

### Improvements

• Improved share validation
• Optimized statistics queries

### Bug Fixes

• Fixed VarDiff job difficulty synchronization
• Fixed session-bound job validation

### Database

• Added statistics snapshot table
• Added difficulty history

### Documentation

• Added Version 1.0 documentation set
```

---

# Categories

Recommended categories include:

## Added

New functionality.

---

## Changed

Behavior improvements.

---

## Fixed

Bug corrections.

---

## Removed

Deprecated functionality removed.

---

## Security

Security improvements.

---

## Documentation

Documentation additions or corrections.

---

# Database Changes

Record:

- New tables
- New indexes
- Migrations
- Constraints
- Data changes

---

# REST API Changes

Record:

- New endpoints
- Changed endpoints
- Deprecated endpoints
- Response changes

---

# Configuration Changes

Document:

- New environment variables
- Default value changes
- Removed configuration

---

# Breaking Changes

Clearly identify any changes requiring operator action.

Include:

- Migration requirements
- Configuration updates
- API incompatibilities

---

# Documentation Updates

Major documentation additions should be recorded alongside software changes.

---

# Git Tags

Production releases should be tagged.

Example:

```
v1.0.0
```

---

# Development Builds

Development snapshots may use:

```
v1.1.0-dev
```

or

```
v1.1.0-beta
```

---

# Best Practices

- Write for users.
- Keep entries concise.
- Record completed work only.
- Avoid implementation details unless important.
- Link related issues when applicable.

---

# Summary

A consistent changelog provides a reliable historical record of Seymour Pool Engine development and simplifies upgrades, troubleshooting, and release management.

---

# Next Step

Continue with:

**27-CONTRIBUTING.md**

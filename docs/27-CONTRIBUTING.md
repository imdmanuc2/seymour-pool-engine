# Contributing

**Document:** 27-CONTRIBUTING.md

**Version:** 1.0 (Development)

---

# Purpose

This document explains how developers can contribute to the Seymour Pool Engine project.

The goal is to maintain a consistent engineering process while ensuring production quality and long-term maintainability.

---

# Guiding Principles

Contributors should strive to:

- Build production-quality software.
- Keep the codebase understandable.
- Preserve backward compatibility whenever practical.
- Document significant changes.
- Test before submitting changes.
- Complete existing objectives before introducing new features.

---

# Before You Begin

Become familiar with:

- Project Architecture
- Development Guide
- Database Schema
- Native Statistics
- REST API
- Troubleshooting Guide

Understanding the existing architecture helps ensure new work fits naturally into the project.

---

# Development Workflow

Typical workflow:

```
Fork / Clone

↓

Create Branch

↓

Implement

↓

Test

↓

Document

↓

Commit

↓

Push

↓

Open Pull Request
```

---

# Branches

Recommended branch naming:

```
feature/native-statistics

feature/vardiff

bugfix/session-validation

docs/rest-api

refactor/database
```

---

# Coding Standards

Contributors should:

- Use descriptive names.
- Prefer readable code.
- Keep functions focused.
- Avoid unnecessary complexity.
- Follow existing project conventions.

---

# Formatting

Format code before committing.

```bash
ruff format
```

---

# Static Analysis

Run Ruff before submitting changes.

```bash
ruff check
```

Resolve warnings whenever practical.

---

# Testing

Run the relevant test suite before committing.

```bash
pytest
```

Example:

```bash
pytest tests/
```

No new feature should be merged without appropriate tests.

---

# Documentation

Significant features should include documentation updates.

Examples include:

- Architecture
- REST API
- Configuration
- Troubleshooting
- Native Statistics
- SQL Reference

Documentation should evolve alongside the code.

---

# Commit Messages

Write clear commit messages.

Good examples:

```
Add Native Statistics worker endpoint

Fix VarDiff job synchronization

Improve share validation logging
```

Avoid:

```
Fix

Stuff

Update
```

---

# Pull Requests

A pull request should include:

- Summary
- Motivation
- Testing performed
- Documentation updates
- Migration notes (if applicable)

---

# Database Changes

Schema modifications must use migrations.

Do not manually modify production schemas.

Migration scripts should be:

- Repeatable
- Reviewed
- Tested

---

# API Changes

REST API changes should:

- Preserve compatibility
- Use consistent JSON
- Document new endpoints
- Include example requests

---

# Performance

Performance improvements should be supported by measurements.

Avoid speculative optimization.

Measure before and after changes whenever possible.

---

# Logging

New functionality should produce meaningful operational logs.

Useful log events include:

- Startup
- Shutdown
- Worker authorization
- Job issuance
- Difficulty changes
- Share validation
- Errors

---

# Security

Never commit:

- Passwords
- RPC credentials
- API keys
- Private certificates
- Production environment files

Sensitive information belongs in deployment-specific configuration.

---

# Version 1.0 Scope

The primary objective is completing a stable Version 1.0 release.

Ideas beyond Version 1.0 should be captured in the roadmap rather than interrupting the current release.

---

# Code Reviews

Reviewers should evaluate:

- Correctness
- Readability
- Maintainability
- Performance
- Testing
- Documentation
- Backward compatibility

The goal is to improve the project rather than simply approve changes.

---

# Issue Reporting

Useful reports include:

- Clear description
- Reproduction steps
- Expected behavior
- Actual behavior
- Relevant logs
- Version information

Detailed reports significantly reduce troubleshooting time.

---

# Community

Contributors are encouraged to:

- Ask questions.
- Improve documentation.
- Report bugs.
- Suggest enhancements.
- Share operational experience.

Constructive collaboration improves the project for everyone.

---

# Summary

Consistent engineering practices help ensure that Seymour Pool Engine remains reliable, maintainable, and production-ready as the platform continues to grow.

---

# Next Step

Continue with:

**28-ROADMAP.md**

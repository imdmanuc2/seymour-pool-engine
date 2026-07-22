# Package 027 — Native Stratum ASIC Compatibility

Adds modern ASIC compatibility to Seymour Native Stratum.

## Features

- BIP320 Version Rolling negotiation
- Supported mask negotiation
- Session capability tracking
- Modern ASIC compatibility
- Regression tests

## Supported Version Rolling Mask

1fffe000

## Workflow

scripts/doctor.sh
scripts/install.sh
scripts/verify.sh

## Status

Validated with:

- Ruff
- 153 passing tests
- Live ASIC packet capture

This package resolves the ASIC disconnect that occurred after
`mining.configure` when Seymour advertised
`"version-rolling": false`.


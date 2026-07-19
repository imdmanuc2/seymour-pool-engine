# Package 001B — Provider Foundation

Run from the extracted package directory:

```bash
chmod +x scripts/*.sh
./scripts/doctor.sh
./scripts/install.sh
./scripts/verify.sh
```

The installer determines the repository root automatically from:

`<repo>/packages/001b-provider-foundation`

It backs up replaced files under `packages/backups/`, copies only the package payload, installs the editable Python project, applies migration 002, and runs verification.

It does not replace `.env`.

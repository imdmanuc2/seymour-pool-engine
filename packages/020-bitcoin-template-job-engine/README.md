# Package 020 — Bitcoin Template & Job Engine

Replaces synthetic Stratum jobs with Bitcoin Core `getblocktemplate` jobs.

Adds:
- authenticated Bitcoin JSON-RPC client;
- block-template parsing and persistence;
- coinbase transaction split around extranonce fields;
- transaction merkle-branch construction;
- Stratum `mining.notify` job creation;
- template status and manual refresh API endpoints;
- migration 021 and focused tests.

## Required environment

```dotenv
SEYMOUR_BITCOIN_RPC_URL=http://127.0.0.1:8332
SEYMOUR_BITCOIN_RPC_USER=<rpc-user>
SEYMOUR_BITCOIN_RPC_PASSWORD=<rpc-password>
SEYMOUR_BITCOIN_PAYOUT_SCRIPT=51
```

`SEYMOUR_BITCOIN_PAYOUT_SCRIPT=51` is a development-only OP_TRUE output. Replace it with the scriptPubKey of the pool payout address before production mining.

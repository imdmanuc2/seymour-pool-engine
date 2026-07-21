from typing import Any

from fastapi import APIRouter, HTTPException

from seymour_pool_engine.providers.bitcoin import BitcoinRpcError
from seymour_pool_engine.services.template_job_service import TemplateJobService

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/status")
def status() -> dict[str, Any]:
    return TemplateJobService().status()


@router.post("/refresh")
def refresh() -> dict[str, Any]:
    try:
        job = TemplateJobService().refresh()
    except (BitcoinRpcError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "jobId": job.job_id,
        "height": job.template_height,
        "previousBlockHash": job.previous_block_hash,
        "transactionCount": job.transaction_count,
        "coinbaseValue": job.coinbase_value,
        "cleanJobs": job.clean_jobs,
    }

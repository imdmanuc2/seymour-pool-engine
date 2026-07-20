from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from seymour_pool_engine.database import engine_connection


class EconomicsRepository:
    def upsert_fee_profile(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO seymour_engine.fee_profiles (
                    fee_profile_id, pool_id, coin, developer_fee_percent,
                    developer_destination, operator_fee_percent, operator_destination
                ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (pool_id, coin) DO UPDATE SET
                    developer_fee_percent=EXCLUDED.developer_fee_percent,
                    developer_destination=EXCLUDED.developer_destination,
                    operator_fee_percent=EXCLUDED.operator_fee_percent,
                    operator_destination=EXCLUDED.operator_destination,
                    updated_at=NOW()
                RETURNING *
            """, (uuid4(), values["pool_id"], values["coin"], values["developer_fee_percent"],
                  values["developer_destination"], values["operator_fee_percent"],
                  values["operator_destination"]))
            row=dict(cursor.fetchone()); connection.commit(); return row

    def get_fee_profile(self, *, pool_id: str, coin: str) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM seymour_engine.fee_profiles WHERE pool_id=%s AND coin=%s", (pool_id, coin))
            row=cursor.fetchone(); return dict(row) if row else None

    def latest_integrity_hash(self, *, pool_id: str, coin: str) -> str | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute("""SELECT integrity_hash FROM seymour_engine.reward_calculations
                              WHERE pool_id=%s AND coin=%s ORDER BY created_at DESC LIMIT 1""", (pool_id, coin))
            row=cursor.fetchone(); return row["integrity_hash"] if row else None

    def create_calculation(self, *, block_id: UUID, fee_profile_id: UUID, pool_id: str,
                           coin: str, policy: str, gross_reward: Decimal,
                           developer_fee_percent: Decimal, operator_fee_percent: Decimal,
                           allocations: list[dict[str, Any]], integrity_hash: str,
                           previous_integrity_hash: str | None) -> dict[str, Any]:
        calculation_id=uuid4()
        developer=next(x["amount"] for x in allocations if x["allocation_type"]=="developer")
        operator=sum((x["amount"] for x in allocations if x["allocation_type"]=="operator"), Decimal("0"))
        workers=sum((x["amount"] for x in allocations if x["allocation_type"]=="worker"), Decimal("0"))
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute("""INSERT INTO seymour_engine.reward_calculations (
                reward_calculation_id, block_id, fee_profile_id, pool_id, coin, policy,
                gross_reward, developer_fee_percent, developer_fee_amount,
                operator_fee_percent, operator_fee_amount, worker_reward_amount,
                integrity_hash, previous_integrity_hash) VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (block_id) DO NOTHING RETURNING reward_calculation_id""",
                (calculation_id, block_id, fee_profile_id, pool_id, coin, policy, gross_reward,
                 developer_fee_percent, developer, operator_fee_percent, operator, workers,
                 integrity_hash, previous_integrity_hash))
            inserted=cursor.fetchone()
            if inserted is None:
                cursor.execute("SELECT reward_calculation_id, integrity_hash FROM seymour_engine.reward_calculations WHERE block_id=%s", (block_id,))
                existing=dict(cursor.fetchone()); return {"rewardCalculationId": str(existing["reward_calculation_id"]), "created": False}
            for item in allocations:
                cursor.execute("""INSERT INTO seymour_engine.reward_allocations (
                    reward_allocation_id, reward_calculation_id, allocation_type,
                    recipient_key, amount, weight, idempotency_key, metadata)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (uuid4(), calculation_id, item["allocation_type"], item["recipient_key"],
                     item["amount"], item["weight"],
                     f"economics:{calculation_id}:{item['allocation_type']}:{item['recipient_key']}", Jsonb({})))
            cursor.execute("""INSERT INTO seymour_engine.reward_calculation_events
                (reward_calculation_event_id, reward_calculation_id, event_type, integrity_hash, metadata)
                VALUES (%s,%s,'calculated',%s,%s)""", (uuid4(), calculation_id, integrity_hash, Jsonb({})))
            connection.commit()
        return {"rewardCalculationId": str(calculation_id), "created": True}

    def economics_summary(self, *, pool_id: str | None, coin: str | None) -> dict[str, Any]:
        where=[]; params=[]
        if pool_id: where.append("pool_id=%s"); params.append(pool_id)
        if coin: where.append("coin=%s"); params.append(coin)
        clause=(" WHERE "+" AND ".join(where)) if where else ""
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(f"""SELECT COUNT(*) AS calculation_count,
                COALESCE(SUM(gross_reward),0) AS gross_reward,
                COALESCE(SUM(developer_fee_amount),0) AS developer_fees,
                COALESCE(SUM(operator_fee_amount),0) AS operator_fees,
                COALESCE(SUM(worker_reward_amount),0) AS worker_rewards
                FROM seymour_engine.reward_calculations{clause}""", tuple(params))
            row=dict(cursor.fetchone())
        return {"poolId": pool_id, "coin": coin, "calculationCount": row["calculation_count"],
                "grossReward": float(row["gross_reward"]), "developerFees": float(row["developer_fees"]),
                "operatorFees": float(row["operator_fees"]), "workerRewards": float(row["worker_rewards"]),
                "minimumDeveloperFeePercent": 0.75}

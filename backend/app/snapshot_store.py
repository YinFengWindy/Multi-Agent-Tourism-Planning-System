from typing import Any

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:  # pragma: no cover
    AsyncIOMotorClient = None

from app.models import PlanEnvelope, PlanSummary
from app.plan_store import build_plan_summary


class MemorySnapshotStore:
    def __init__(self) -> None:
        self.snapshots: dict[str, dict[str, Any]] = {}

    async def save_plan(self, envelope: PlanEnvelope) -> None:
        self.snapshots[envelope.plan_id] = envelope.model_dump(mode="json")

    async def get_plan(self, plan_id: str) -> PlanEnvelope | None:
        document = self.snapshots.get(plan_id)
        if not document:
            return None
        return PlanEnvelope.model_validate(document)

    async def list_plan_summaries(self, limit: int = 8) -> list[PlanSummary]:
        summaries = [
            build_plan_summary(PlanEnvelope.model_validate(document))
            for document in self.snapshots.values()
        ]
        return sorted(summaries, key=lambda item: item.updated_at, reverse=True)[:limit]


class MongoSnapshotStore:
    def __init__(self, client: Any, db_name: str) -> None:
        self._collection = client[db_name]["plan_snapshots"]

    async def save_plan(self, envelope: PlanEnvelope) -> None:
        document = envelope.model_dump(mode="json")
        await self._collection.update_one(
            {"plan_id": envelope.plan_id},
            {"$set": document},
            upsert=True,
        )

    async def get_plan(self, plan_id: str) -> PlanEnvelope | None:
        document = await self._collection.find_one({"plan_id": plan_id}, {"_id": 0})
        if not document:
            return None
        return PlanEnvelope.model_validate(document)

    async def list_plan_summaries(self, limit: int = 8) -> list[PlanSummary]:
        documents = await self._collection.find({}, {"_id": 0}).sort("updated_at", -1).to_list(length=limit)
        return [build_plan_summary(PlanEnvelope.model_validate(document)) for document in documents]


async def create_snapshot_store(mongodb_uri: str, db_name: str) -> MemorySnapshotStore | MongoSnapshotStore:
    if AsyncIOMotorClient and mongodb_uri:
        try:
            client = AsyncIOMotorClient(mongodb_uri, serverSelectionTimeoutMS=1500)
            await client.admin.command("ping")
            return MongoSnapshotStore(client, db_name)
        except Exception:
            return MemorySnapshotStore()
    return MemorySnapshotStore()

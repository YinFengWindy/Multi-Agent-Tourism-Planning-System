from typing import Any

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:  # pragma: no cover
    AsyncIOMotorClient = None

from app.models import PlanEnvelope


class MemorySnapshotStore:
    def __init__(self) -> None:
        self.snapshots: dict[str, dict[str, Any]] = {}

    async def save_plan(self, envelope: PlanEnvelope) -> None:
        self.snapshots[envelope.plan_id] = envelope.model_dump(mode="json")


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


async def create_snapshot_store(mongodb_uri: str, db_name: str) -> MemorySnapshotStore | MongoSnapshotStore:
    if AsyncIOMotorClient and mongodb_uri:
        try:
            client = AsyncIOMotorClient(mongodb_uri, serverSelectionTimeoutMS=1500)
            await client.admin.command("ping")
            return MongoSnapshotStore(client, db_name)
        except Exception:
            return MemorySnapshotStore()
    return MemorySnapshotStore()


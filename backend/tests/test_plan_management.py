import asyncio

import pytest

from app.models import DayItem, DayPlan, PlanRequest, PlanResult, TravelConstraints
from app.plan_store import PlanStore
from app.snapshot_store import MemorySnapshotStore
from apps.planner_service.main import _merge_recent_plans


def make_request(origin: str, destination: str, budget: float = 3000) -> PlanRequest:
    return PlanRequest(
        origin_city=origin,
        destination_cities=[destination],
        start_date='2026-05-01',
        end_date='2026-05-02',
        travelers=2,
        budget=budget,
        preferences=['美食'],
        constraints=TravelConstraints(),
    )


def make_result(plan_id: str, city: str, summary: str) -> PlanResult:
    return PlanResult(
        plan_id=plan_id,
        summary=summary,
        days=[
            DayPlan(
                day_index=1,
                date='2026-05-01',
                city=city,
                theme='城市探索',
                items=[DayItem(time='10:00', title='抵达', description='进入主行程')],
            )
        ],
        warnings=['天气提醒'],
    )


@pytest.mark.asyncio
async def test_plan_store_lists_recent_summaries_sorted() -> None:
    store = PlanStore()
    first = await store.create_plan(make_request('上海', '杭州', 3200))
    await asyncio.sleep(0.01)
    second = await store.create_plan(make_request('北京', '苏州', 4200))

    await store.complete(first.plan_id, make_result(first.plan_id, '杭州', '首个规划'))
    await asyncio.sleep(0.01)
    await store.complete(second.plan_id, make_result(second.plan_id, '苏州', '第二个规划'))

    summaries = await store.list_summaries()

    assert [item.plan_id for item in summaries[:2]] == [second.plan_id, first.plan_id]
    assert summaries[0].summary == '第二个规划'
    assert summaries[0].warning_count == 1
    assert summaries[0].day_count == 1


@pytest.mark.asyncio
async def test_memory_snapshot_store_returns_plan_summaries() -> None:
    store = MemorySnapshotStore()
    envelope_store = PlanStore()
    envelope = await envelope_store.create_plan(make_request('广州', '深圳', 2800))
    await envelope_store.complete(envelope.plan_id, make_result(envelope.plan_id, '深圳', '湾区周末游'))
    completed = await envelope_store.get(envelope.plan_id)

    assert completed is not None
    await store.save_plan(completed)

    summaries = await store.list_plan_summaries()

    assert len(summaries) == 1
    assert summaries[0].origin_city == '广州'
    assert summaries[0].summary == '湾区周末游'


@pytest.mark.asyncio
async def test_memory_snapshot_store_can_restore_plan_by_id() -> None:
    snapshot_store = MemorySnapshotStore()
    envelope_store = PlanStore()
    envelope = await envelope_store.create_plan(make_request('南京', '苏州', 3600))
    await envelope_store.complete(envelope.plan_id, make_result(envelope.plan_id, '苏州', '江南慢游'))
    completed = await envelope_store.get(envelope.plan_id)

    assert completed is not None
    await snapshot_store.save_plan(completed)

    restored = await snapshot_store.get_plan(envelope.plan_id)

    assert restored is not None
    assert restored.plan_id == envelope.plan_id
    assert restored.result is not None
    assert restored.result.summary == '江南慢游'


@pytest.mark.asyncio
async def test_plan_store_restore_plan_rehydrates_memory() -> None:
    source_store = PlanStore()
    target_store = PlanStore()
    envelope = await source_store.create_plan(make_request('成都', '重庆', 2600))
    await source_store.complete(envelope.plan_id, make_result(envelope.plan_id, '重庆', '双城周末'))
    completed = await source_store.get(envelope.plan_id)

    assert completed is not None
    await target_store.restore_plan(completed)

    restored = await target_store.get(envelope.plan_id)

    assert restored is not None
    assert restored.result is not None
    assert restored.result.summary == '双城周末'


def test_merge_recent_plans_deduplicates_by_latest_update() -> None:
    newer = make_result('plan_same', '杭州', '新摘要')
    older = make_result('plan_same', '杭州', '旧摘要')

    newer_summary = newer.model_copy(update={
        'plan_id': 'plan_same',
    })
    older_summary = older.model_copy(update={
        'plan_id': 'plan_same',
    })

    active_store = PlanStore()
    snapshot_store = PlanStore()

    async def build_summaries():
        active_envelope = await active_store.create_plan(make_request('上海', '杭州'))
        await active_store.complete(active_envelope.plan_id, make_result(active_envelope.plan_id, '杭州', '新摘要'))
        active = await active_store.list_summaries()

        snapshot_envelope = await snapshot_store.create_plan(make_request('上海', '杭州'))
        await snapshot_store.complete(snapshot_envelope.plan_id, make_result(snapshot_envelope.plan_id, '杭州', '旧摘要'))
        snapshots = await snapshot_store.list_summaries()
        snapshots[0].plan_id = active[0].plan_id
        snapshots[0].updated_at = active[0].updated_at
        snapshots[0].summary = '旧摘要'
        return active, snapshots

    active, snapshots = asyncio.run(build_summaries())
    merged = _merge_recent_plans(active, snapshots, 8)

    assert len(merged) == 1
    assert merged[0].summary == '新摘要'

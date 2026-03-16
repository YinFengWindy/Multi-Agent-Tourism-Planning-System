import asyncio
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from app.models import AgentTaskRequest, BudgetBreakdown, DayItem, DayPlan, DomainInsight, PlanRequest, PlanResult

EventEmitter = Callable[[str, str, dict[str, Any]], Awaitable[None]]
AgentExecutor = Callable[[AgentTaskRequest], Awaitable[DomainInsight]]


class PlanningState(TypedDict, total=False):
    request: PlanRequest
    attempts: int
    insights: dict[str, DomainInsight]
    warnings: list[str]
    replan_reason: str
    needs_replan: bool
    result: PlanResult


def _build_dates(start_date: str, end_date: str) -> list[str]:
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        days = max(1, (end - start).days + 1)
        return [(start + timedelta(days=offset)).strftime("%Y-%m-%d") for offset in range(days)]
    except ValueError:
        return [start_date]


def _city_sequence(request: PlanRequest, day_count: int) -> list[str]:
    cities = request.destination_cities or [request.origin_city]
    return [cities[min(index, len(cities) - 1)] for index in range(day_count)]


class PlanningEngine:
    def __init__(self, agent_executor: AgentExecutor) -> None:
        self._agent_executor = agent_executor

    async def create_plan(
        self,
        plan_id: str,
        request: PlanRequest,
        version: int,
        emit: EventEmitter,
    ) -> PlanResult:
        graph = self._build_graph(plan_id, version, emit)
        result = await graph.ainvoke({"request": request, "attempts": 0, "insights": {}, "warnings": []})
        return result["result"]

    def _build_graph(self, plan_id: str, version: int, emit: EventEmitter):
        async def collect_constraints(state: PlanningState) -> PlanningState:
            request = state["request"]
            if not request.destination_cities:
                request.destination_cities = [request.origin_city]
            await emit(
                "plan_started",
                "Parent Agent 已开始解析约束并构建协同任务图。",
                {"plan_id": plan_id, "version": version},
            )
            return state

        async def dispatch_agents(state: PlanningState) -> PlanningState:
            request = state["request"]
            agent_types = ["transport", "hotel", "route", "attraction", "budget", "risk"]
            await emit(
                "task_dispatched",
                "已并行派发交通、住宿、路线、景点、预算、风险六类子任务。",
                {"agent_types": agent_types, "attempt": state["attempts"] + 1},
            )
            tasks = [
                AgentTaskRequest(
                    task_id=f"{plan_id}_{agent_type}_{state['attempts'] + 1}",
                    plan_id=plan_id,
                    agent_type=agent_type,
                    goal=f"围绕 {', '.join(request.destination_cities)} 生成 {agent_type} 领域建议",
                    request=request,
                    shared_context={"attempt": state["attempts"] + 1},
                )
                for agent_type in agent_types
            ]
            results = await asyncio.gather(*[self._agent_executor(task) for task in tasks])
            insights = {result.agent_type: result for result in results}
            for result in results:
                await emit(
                    "agent_progress",
                    f"{result.agent_type} Agent 已返回：{result.summary}",
                    {"agent_type": result.agent_type, "highlights": result.highlights[:2]},
                )
            state["insights"] = insights
            return state

        async def quality_gate(state: PlanningState) -> PlanningState:
            insights = state["insights"]
            budget_insight = insights.get("budget")
            risk_insight = insights.get("risk")
            warnings: list[str] = []
            for insight in insights.values():
                warnings.extend(insight.warnings)

            over_budget = not budget_insight.structured_data.get("within_budget", True) if budget_insight else False
            weather_risk = any("降雨风险" in warning for warning in (risk_insight.warnings if risk_insight else []))
            needs_replan = state["attempts"] < 1 and (over_budget or weather_risk)
            state["warnings"] = list(dict.fromkeys(warnings))
            state["needs_replan"] = needs_replan
            state["replan_reason"] = "budget_or_risk" if needs_replan else "ok"
            if needs_replan:
                await emit(
                    "replan_triggered",
                    "质量闸门检测到预算或天气风险，Parent Agent 正在自动重规划。",
                    {"warnings": state["warnings"]},
                )
            return state

        async def replan(state: PlanningState) -> PlanningState:
            request = state["request"].model_copy(deep=True)
            request.constraints.hotel_level = "经济型"
            if "室内体验" not in request.preferences:
                request.preferences.append("室内体验")
            request.constraints.budget_mode = "tight"
            state["request"] = request
            state["attempts"] += 1
            await emit(
                "agent_progress",
                "已切换为更紧凑预算模式，并为天气风险追加室内候选点。",
                {"hotel_level": request.constraints.hotel_level, "budget_mode": request.constraints.budget_mode},
            )
            return state

        async def finalize(state: PlanningState) -> PlanningState:
            request = state["request"]
            insights = state["insights"]
            dates = _build_dates(request.start_date, request.end_date)
            cities = _city_sequence(request, len(dates))
            route_plans = insights.get("route", DomainInsight(agent_type="route", summary="")).structured_data.get(
                "city_plans", []
            )
            attractions = insights.get(
                "attraction", DomainInsight(agent_type="attraction", summary="")
            ).structured_data.get("pois_by_city", {})
            hotel_options = insights.get("hotel", DomainInsight(agent_type="hotel", summary="")).structured_data.get(
                "options", []
            )
            transport_options = insights.get(
                "transport", DomainInsight(agent_type="transport", summary="")
            ).structured_data.get("options", [])
            budget_data = insights.get("budget", DomainInsight(agent_type="budget", summary="")).structured_data.get(
                "breakdown", {}
            )

            days: list[DayPlan] = []
            for index, date in enumerate(dates, start=1):
                city = cities[index - 1]
                route_plan = next((item for item in route_plans if item.get("city") == city), None)
                poi_names = route_plan.get("recommended_pois", []) if route_plan else []
                if not poi_names:
                    poi_names = [poi.get("name", "城市漫步") for poi in attractions.get(city, [])[:3]]
                items = [
                    DayItem(time="09:30-11:30", title=f"{poi_names[0] if poi_names else city} 探索", description="上午核心景点游览。"),
                    DayItem(time="12:00-13:30", title="在地午餐", description="根据偏好选择口碑餐厅与休息点。"),
                    DayItem(
                        time="14:00-17:30",
                        title=f"{poi_names[1] if len(poi_names) > 1 else city + ' 城市漫步'}",
                        description="下午安排次核心景点或街区步行路线。",
                    ),
                ]
                hotel_tip = hotel_options[0]["name"] if hotel_options else f"建议入住 {city} 核心交通区"
                transport_tip = (
                    f"优先选择 {transport_options[0]['mode']}，出发时间 {transport_options[0]['depart_time']}"
                    if transport_options
                    else "优先公共交通 + 步行衔接"
                )
                days.append(
                    DayPlan(
                        day_index=index,
                        date=date,
                        city=city,
                        theme=(route_plan or {}).get("theme", f"{city} 经典游览"),
                        items=items,
                        hotel_tip=hotel_tip,
                        transport_tip=transport_tip,
                    )
                )

            result = PlanResult(
                plan_id=plan_id,
                summary=f"{', '.join(request.destination_cities)} {len(days)} 天多 Agent 协同旅游方案",
                days=days,
                budget_breakdown=BudgetBreakdown(**budget_data) if budget_data else BudgetBreakdown(),
                transport_options=transport_options,
                hotel_options=hotel_options,
                warnings=list(dict.fromkeys(state.get("warnings", []))),
                fallback_plans=[
                    "若遇天气波动，切换博物馆 / 室内街区 / 商圈路线。",
                    "若预算继续收紧，可进一步下调酒店档位并减少收费景点。",
                ],
                domain_insights=insights,
                version=version,
            )
            state["result"] = result
            await emit(
                "agent_progress",
                "Parent Agent 已完成结果聚合与行程成品生成。",
                {"days": len(days), "warnings": result.warnings[:2]},
            )
            return state

        def route_after_quality_gate(state: PlanningState) -> str:
            return "replan" if state.get("needs_replan") else "finalize"

        graph = StateGraph(PlanningState)
        graph.add_node("collect_constraints", collect_constraints)
        graph.add_node("dispatch_agents", dispatch_agents)
        graph.add_node("quality_gate", quality_gate)
        graph.add_node("replan", replan)
        graph.add_node("finalize", finalize)
        graph.set_entry_point("collect_constraints")
        graph.add_edge("collect_constraints", "dispatch_agents")
        graph.add_edge("dispatch_agents", "quality_gate")
        graph.add_conditional_edges(
            "quality_gate",
            route_after_quality_gate,
            {"replan": "replan", "finalize": "finalize"},
        )
        graph.add_edge("replan", "dispatch_agents")
        graph.add_edge("finalize", END)
        return graph.compile()


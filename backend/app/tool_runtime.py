import asyncio
import hashlib
import json
import random
from time import perf_counter
from typing import Any

from app.models import ToolExecutionRequest, ToolExecutionResponse


CITY_DATA = {
    "上海": {
        "districts": ["外滩", "静安寺", "徐家汇"],
        "pois": ["外滩", "豫园", "东方明珠", "武康路", "上海博物馆"],
        "hotel_base": 520,
    },
    "杭州": {
        "districts": ["西湖东", "武林广场", "滨江"],
        "pois": ["西湖", "灵隐寺", "西溪湿地", "河坊街", "法喜寺"],
        "hotel_base": 420,
    },
    "乌镇": {
        "districts": ["西栅", "东栅", "景区外沿河"],
        "pois": ["乌镇西栅", "乌镇东栅", "木心美术馆", "昭明书院"],
        "hotel_base": 360,
    },
    "苏州": {
        "districts": ["观前街", "平江路", "金鸡湖"],
        "pois": ["拙政园", "平江路", "山塘街", "金鸡湖"],
        "hotel_base": 410,
    },
    "北京": {
        "districts": ["王府井", "国贸", "前门"],
        "pois": ["故宫", "天坛", "颐和园", "南锣鼓巷"],
        "hotel_base": 560,
    },
}

DEFAULT_POIS = ["城市博物馆", "历史街区", "城市公园", "地标观景台"]
WEATHER_CONDITIONS = ["晴", "多云", "小雨", "阵雨"]


def _seed(*parts: Any) -> int:
    joined = "|".join(str(part) for part in parts)
    return int(hashlib.md5(joined.encode("utf-8")).hexdigest()[:8], 16)


def _profile(city: str) -> dict[str, Any]:
    return CITY_DATA.get(
        city,
        {"districts": ["市中心", "老城区", "交通枢纽附近"], "pois": DEFAULT_POIS, "hotel_base": 350},
    )


def _weather(arguments: dict[str, Any]) -> tuple[dict[str, Any], str]:
    city = arguments.get("city", "目的地")
    date = arguments.get("date", "待定日期")
    seeded = _seed(city, date)
    randomizer = random.Random(seeded)
    condition = WEATHER_CONDITIONS[seeded % len(WEATHER_CONDITIONS)]
    high = randomizer.randint(18, 31)
    low = high - randomizer.randint(5, 9)
    risk_level = "medium" if condition in {"小雨", "阵雨"} else "low"
    advice = "建议预留室内备选景点" if risk_level == "medium" else "适合户外游览"
    data = {
        "city": city,
        "date": date,
        "condition": condition,
        "temperature": {"low": low, "high": high},
        "risk_level": risk_level,
        "advice": advice,
    }
    summary = f"{city}{date}天气{condition}，{low}~{high}℃，{advice}。"
    return data, summary


def _transport(arguments: dict[str, Any]) -> tuple[dict[str, Any], str]:
    origin = arguments.get("origin", "出发地")
    destination = arguments.get("destination", "目的地")
    travelers = int(arguments.get("travelers", 1))
    seeded = _seed(origin, destination, travelers)
    randomizer = random.Random(seeded)
    base_price = 68 + seeded % 60
    options = []
    for index, mode in enumerate(["高铁", "动车", "城际巴士"]):
        depart_hour = 7 + index * 2
        duration = 55 + randomizer.randint(20, 90)
        price = base_price + index * 22
        options.append(
            {
                "mode": mode,
                "depart_time": f"{depart_hour:02d}:{randomizer.randint(0, 1) * 5:02d}",
                "arrive_time": f"{(depart_hour + duration // 60) % 24:02d}:{duration % 60:02d}",
                "duration_minutes": duration,
                "price": price,
                "score": round(9.3 - index * 0.6, 1),
            }
        )
    cheapest = min(options, key=lambda item: item["price"])
    data = {"origin": origin, "destination": destination, "options": options}
    summary = (
        f"{origin}到{destination}共生成 {len(options)} 条候选，"
        f"最低单人票价 {cheapest['price']} 元，推荐 {options[0]['mode']}。"
    )
    return data, summary


def _hotel(arguments: dict[str, Any]) -> tuple[dict[str, Any], str]:
    city = arguments.get("city", "目的地")
    nights = max(1, int(arguments.get("nights", 1)))
    profile = _profile(city)
    seeded = _seed(city, nights, arguments.get("hotel_level", "舒适型"))
    randomizer = random.Random(seeded)
    hotels = []
    for index, district in enumerate(profile["districts"]):
        nightly_price = profile["hotel_base"] + index * 55 + randomizer.randint(-25, 35)
        hotels.append(
            {
                "name": f"{district}旅居酒店 {index + 1}",
                "district": district,
                "nightly_price": nightly_price,
                "rating": round(4.8 - index * 0.2, 1),
                "commute_score": round(9.2 - index * 0.4, 1),
                "stay_total": nightly_price * nights,
            }
        )
    best = hotels[0]
    data = {"city": city, "nights": nights, "options": hotels}
    summary = f"{city}住宿推荐 {len(hotels)} 家，首选 {best['name']}，总价约 {best['stay_total']} 元。"
    return data, summary


def _poi(arguments: dict[str, Any]) -> tuple[dict[str, Any], str]:
    city = arguments.get("city", "目的地")
    preferences = arguments.get("preferences", [])
    profile = _profile(city)
    pois = []
    for index, name in enumerate(profile["pois"]):
        tags = [preferences[index % len(preferences)]] if preferences else ["人文", "城市漫步"][index % 2 : index % 2 + 1]
        pois.append(
            {
                "name": name,
                "open_time": "09:00-18:00",
                "ticket_price": 0 if index == 0 else 40 + index * 15,
                "recommended_visit_hours": 2 + index % 2,
                "tags": tags,
            }
        )
    data = {"city": city, "pois": pois}
    summary = f"{city}筛选出 {len(pois)} 个候选景点，优先推荐 {pois[0]['name']}。"
    return data, summary


def _route_matrix(arguments: dict[str, Any]) -> tuple[dict[str, Any], str]:
    city = arguments.get("city", "目的地")
    pois = arguments.get("pois", [])
    seeded = _seed(city, json.dumps(pois, ensure_ascii=False))
    randomizer = random.Random(seeded)
    ordered = list(pois)
    matrix = []
    for start in ordered:
        row = []
        for end in ordered:
            row.append(0 if start == end else randomizer.randint(12, 38))
        matrix.append(row)
    data = {
        "city": city,
        "recommended_order": ordered,
        "travel_minutes_matrix": matrix,
        "walking_intensity": "moderate" if len(ordered) >= 3 else "light",
    }
    summary = f"{city}生成 {len(ordered)} 个点位的路线矩阵，建议顺序：{' → '.join(ordered)}。"
    return data, summary


HANDLERS = {
    "weather_forecast": _weather,
    "transport_search": _transport,
    "hotel_search": _hotel,
    "poi_search": _poi,
    "route_matrix": _route_matrix,
}


async def execute_tool(request: ToolExecutionRequest, cache: Any | None = None) -> ToolExecutionResponse:
    cache_key = (
        f"tool:{request.tool_name}:"
        f"{hashlib.md5(json.dumps(request.arguments, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()}"
    )
    if cache:
        cached = await cache.get_json(cache_key)
        if cached:
            response = ToolExecutionResponse.model_validate(cached)
            response.cached = True
            return response

    started_at = perf_counter()
    await asyncio.sleep(0.05)

    if request.tool_name not in HANDLERS:
        return ToolExecutionResponse(
            success=False,
            latency_ms=int((perf_counter() - started_at) * 1000),
            data={"error": f"unsupported tool: {request.tool_name}"},
            normalized_summary=f"工具 {request.tool_name} 暂不支持。",
        )

    data, summary = HANDLERS[request.tool_name](request.arguments)
    response = ToolExecutionResponse(
        success=True,
        latency_ms=int((perf_counter() - started_at) * 1000),
        data=data,
        normalized_summary=summary,
    )
    if cache:
        await cache.set_json(cache_key, response.model_dump(mode="json"), ttl_seconds=3600)
    return response


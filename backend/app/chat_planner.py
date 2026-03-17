import json
import re
from typing import Any

import httpx

from app.models import ChatMessage, LlmConnectionConfig, PlanRequest, TravelConstraints

SYSTEM_PROMPT = """
你是 AI Tourism Workspace 的对话规划助手。

你的职责：
1. 用自然中文与用户对话，理解旅游规划需求。
2. 当信息不足时，提出一个最关键的追问。
3. 当信息足够时，提取结构化规划请求。
4. 如果用户是在已有方案上修改，则输出 replan 所需的 updated_constraints。

你必须只输出 JSON，不要输出 markdown，不要输出解释。

输出格式：
{
  "assistant_reply": "给用户显示的自然语言回复",
  "action": "ask" | "create_plan" | "replan",
  "request": PlanRequest 或 null,
  "updated_constraints": { ... } 或 {}
}

规则：
- action=ask：当信息不足，assistant_reply 必须是追问。
- action=create_plan：request 必须是完整 PlanRequest。
- action=replan：仅在已有 current_plan_id 且用户明确想修改既有方案时使用。
- 日期使用 YYYY-MM-DD。
- destination_cities / preferences / transport_mode 必须是数组。
- constraints 缺失时使用默认值补齐。
""".strip()


def normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip('/')
    if normalized.endswith('/chat/completions'):
        normalized = normalized[: -len('/chat/completions')]
    return normalized


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```[a-zA-Z0-9_-]*\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)

    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]

    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError('LLM 输出不是 JSON 对象')
    return payload


def _normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        parts = re.split(r'[,，/\n]+', value)
        return [item.strip() for item in parts if item.strip()]
    return []


def coerce_plan_request(payload: Any) -> PlanRequest | None:
    if not isinstance(payload, dict):
        return None

    constraints_defaults = TravelConstraints().model_dump()
    constraints_input = payload.get('constraints') if isinstance(payload.get('constraints'), dict) else {}

    merged_payload = {
        'origin_city': str(payload.get('origin_city', '')).strip(),
        'destination_cities': _normalize_string_list(payload.get('destination_cities')),
        'start_date': str(payload.get('start_date', '')).strip(),
        'end_date': str(payload.get('end_date', '')).strip(),
        'travelers': int(payload.get('travelers', 1) or 1),
        'budget': float(payload.get('budget', 3000) or 3000),
        'preferences': _normalize_string_list(payload.get('preferences')),
        'constraints': {
            **constraints_defaults,
            **constraints_input,
            'transport_mode': _normalize_string_list(
                constraints_input.get('transport_mode', constraints_defaults['transport_mode'])
            )
            or constraints_defaults['transport_mode'],
        },
    }

    try:
        return PlanRequest.model_validate(merged_payload)
    except Exception:
        return None


def coerce_updated_constraints(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    allowed_keys = {
        'origin_city',
        'destination_cities',
        'start_date',
        'end_date',
        'travelers',
        'budget',
        'preferences',
        'transport_mode',
        'hotel_level',
        'daily_start_after',
        'daily_end_before',
        'budget_mode',
    }

    normalized: dict[str, Any] = {}
    for key, value in payload.items():
        if key not in allowed_keys:
            continue
        if key in {'destination_cities', 'preferences', 'transport_mode'}:
            normalized[key] = _normalize_string_list(value)
        else:
            normalized[key] = value
    return normalized


def _flatten_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                parts.append(str(item.get('text', '')))
        return '\n'.join(parts)
    return str(content)


async def request_chat_decision(
    messages: list[ChatMessage],
    llm_config: LlmConnectionConfig,
    current_request: PlanRequest | None,
    current_plan_id: str | None,
) -> dict[str, Any]:
    system_context = {
        'current_plan_id': current_plan_id,
        'current_request': current_request.model_dump(mode='json') if current_request else None,
    }
    base_url = normalize_base_url(llm_config.base_url)
    request_messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'system', 'content': json.dumps(system_context, ensure_ascii=False)},
        *[message.model_dump(mode='json') for message in messages],
    ]

    async with httpx.AsyncClient(base_url=base_url, timeout=45.0) as client:
        response = await client.post(
            '/chat/completions',
            headers={
                'Authorization': f'Bearer {llm_config.api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': llm_config.model,
                'messages': request_messages,
                'temperature': llm_config.temperature,
            },
        )
        response.raise_for_status()
        payload = response.json()

    content = _flatten_content(payload['choices'][0]['message']['content'])
    parsed = extract_json_object(content)
    action = str(parsed.get('action', 'ask'))
    assistant_reply = str(parsed.get('assistant_reply', '')).strip()
    request_preview = coerce_plan_request(parsed.get('request'))
    updated_constraints = coerce_updated_constraints(parsed.get('updated_constraints'))

    if action == 'create_plan' and request_preview is None:
        action = 'ask'
        assistant_reply = assistant_reply or '我还需要更完整的行程信息，例如目的地、日期、预算和人数。'

    if action == 'replan' and not current_plan_id:
        action = 'ask'
        assistant_reply = assistant_reply or '请先生成一个初始方案，再告诉我你想调整哪些条件。'

    if action not in {'ask', 'create_plan', 'replan'}:
        action = 'ask'

    return {
        'assistant_reply': assistant_reply or '请继续补充你的旅行需求。',
        'action': action,
        'request_preview': request_preview,
        'updated_constraints': updated_constraints,
    }

from app.chat_planner import coerce_plan_request, coerce_updated_constraints, extract_json_object, normalize_base_url


def test_normalize_base_url_trims_chat_completion_path() -> None:
    assert normalize_base_url('https://api.openai.com/v1/chat/completions') == 'https://api.openai.com/v1'


def test_extract_json_object_supports_fenced_payload() -> None:
    payload = extract_json_object('```json\n{"action":"ask","assistant_reply":"请补充日期"}\n```')
    assert payload['action'] == 'ask'
    assert payload['assistant_reply'] == '请补充日期'


def test_coerce_plan_request_normalizes_string_fields() -> None:
    request = coerce_plan_request(
        {
            'origin_city': '上海',
            'destination_cities': '杭州,乌镇',
            'start_date': '2026-05-01',
            'end_date': '2026-05-03',
            'travelers': '2',
            'budget': '4200',
            'preferences': '美食,古镇',
            'constraints': {
                'transport_mode': '高铁,地铁',
                'hotel_level': '舒适型',
            },
        }
    )

    assert request is not None
    assert request.destination_cities == ['杭州', '乌镇']
    assert request.preferences == ['美食', '古镇']
    assert request.constraints.transport_mode == ['高铁', '地铁']


def test_coerce_updated_constraints_filters_unknown_keys() -> None:
    payload = coerce_updated_constraints({'budget': 3200, 'hotel_level': '经济型', 'unsafe': 'x'})
    assert payload == {'budget': 3200, 'hotel_level': '经济型'}

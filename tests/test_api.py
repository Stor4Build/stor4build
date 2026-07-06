# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import json
import os

from fastapi.testclient import TestClient

from stor4build.api import create_app


this_dir = os.path.abspath(os.path.dirname(__file__))
resources_dir = os.path.join(this_dir, '..', 'resources')
schema_path = os.path.join(this_dir, '..', 'schema', 'stor4build.json')


def _normalize_nullable_enum(schema_dict):
    if not isinstance(schema_dict, dict):
        return schema_dict
    if 'anyOf' in schema_dict and 'enum' not in schema_dict:
        enum_values = None
        new_anyof = []
        for option in schema_dict['anyOf']:
            if isinstance(option, dict) and option.get('type') == 'string' and 'enum' in option:
                enum_values = option['enum']
                option = {k: v for k, v in option.items() if k != 'enum'}
            new_anyof.append(option)
        if enum_values is not None:
            schema_dict = dict(schema_dict)
            schema_dict['anyOf'] = new_anyof
            schema_dict['enum'] = enum_values
    return schema_dict


def _normalize_openapi(value):
    if isinstance(value, dict):
        normalized = {}
        for key, child in value.items():
            if key in {'title', 'default'}:
                continue
            normalized[key] = _normalize_openapi(child)

        normalized = _normalize_nullable_enum(normalized)

        if normalized.get('schema') == {}:
            return {}

        content = normalized.get('content')
        if isinstance(content, dict) and content.get('application/json') in ({'schema': {}}, {}) and 'text/csv' in content:
            content = dict(content)
            content.pop('application/json', None)
            normalized['content'] = content

        if 'components' in normalized and 'schemas' in normalized['components']:
            normalized['components']['schemas'].pop('HTTPValidationError', None)
            normalized['components']['schemas'].pop('ValidationError', None)
        return normalized
    if isinstance(value, list):
        return [_normalize_openapi(child) for child in value]
    return value


def test_openapi_schema_matches_file():
    app = create_app()
    current = _normalize_openapi(app.openapi())
    with open(schema_path, 'r') as fp:
        in_repo = _normalize_openapi(json.load(fp))
    assert current == in_repo


def test_simulate_returns_csv(monkeypatch):
    app = create_app(config={
        'TIMESCALE_DB': 'db',
        'TIMESCALE_USERNAME': 'user',
        'TIMESCALE_PASSWORD': 'pass',
    })
    client = TestClient(app)

    def fake_run_simulation_request(payload, settings):
        assert payload.detailed_header is False
        return 'col_a,col_b\n1,2\n'

    monkeypatch.setattr('stor4build.api.run_simulation_request', fake_run_simulation_request)

    with open(os.path.join(resources_dir, 'minimal-input-ice.json'), 'r') as fp:
        payload = json.load(fp)
    payload['header_style'] = 'simple'

    response = client.post('/simulate', json=payload)

    assert response.status_code == 200
    assert response.headers['content-disposition'] == 'attachment; filename=results.csv'
    assert response.headers['content-type'].startswith('text/csv')
    assert response.text == 'col_a,col_b\n1,2\n'


def test_simulate_validation_error():
    app = create_app()
    client = TestClient(app)

    response = client.post('/simulate', json={'baseline': {}, 'storage': {'type': 'not-real'}})

    assert response.status_code == 422
    body = response.json()
    assert body['error'] == 'Bad request'

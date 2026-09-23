def test_health_endpoint_no_auth_required(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.get_json() == {'status': 'ok'}


def test_healthz_alias(client):
    assert client.get('/healthz').status_code == 200


def test_info_endpoint(client):
    resp = client.get('/info')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['topic_list_count'] == 0
    assert body['topic_count'] == 0


def test_api_requires_api_key(client):
    resp = client.get('/api/topic_lists')
    assert resp.status_code == 401


def test_create_and_list_topic_lists(client, api_headers):
    resp = client.post(
        '/api/topic_lists', json={'name': 'Animals', 'description': 'Fun facts', 'reusable': True},
        headers=api_headers,
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body['name'] == 'Animals'

    resp = client.get('/api/topic_lists', headers=api_headers)
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1


def test_create_duplicate_topic_list_rejected(client, api_headers):
    client.post('/api/topic_lists', json={'name': 'Animals'}, headers=api_headers)
    resp = client.post('/api/topic_lists', json={'name': 'Animals'}, headers=api_headers)
    assert resp.status_code == 409


def test_create_topic_list_requires_name(client, api_headers):
    resp = client.post('/api/topic_lists', json={}, headers=api_headers)
    assert resp.status_code == 400


def test_add_topic_and_get_next_topic(client, api_headers):
    create_resp = client.post('/api/topic_lists', json={'name': 'Animals'}, headers=api_headers)
    list_id = create_resp.get_json()['id']

    client.post(f'/api/topic_lists/{list_id}/topics', json={'text': 'Lions'}, headers=api_headers)
    client.post(f'/api/topic_lists/{list_id}/topics', json={'text': 'Tigers'}, headers=api_headers)

    resp = client.get(f'/api/topic_lists/{list_id}/next_topic', headers=api_headers)
    assert resp.status_code == 200
    assert resp.get_json()['text'] in ('Lions', 'Tigers')


def test_next_topic_unknown_strategy_returns_400(client, api_headers):
    create_resp = client.post('/api/topic_lists', json={'name': 'Animals'}, headers=api_headers)
    list_id = create_resp.get_json()['id']
    resp = client.get(
        f'/api/topic_lists/{list_id}/next_topic?strategy=bogus', headers=api_headers
    )
    assert resp.status_code == 400


def test_next_topic_empty_list_returns_404(client, api_headers):
    create_resp = client.post('/api/topic_lists', json={'name': 'Animals'}, headers=api_headers)
    list_id = create_resp.get_json()['id']
    resp = client.get(f'/api/topic_lists/{list_id}/next_topic', headers=api_headers)
    assert resp.status_code == 404


def test_non_reusable_list_deactivates_topic_after_use(client, api_headers):
    create_resp = client.post(
        '/api/topic_lists', json={'name': 'OneShot', 'reusable': False}, headers=api_headers
    )
    list_id = create_resp.get_json()['id']
    client.post(f'/api/topic_lists/{list_id}/topics', json={'text': 'Only one'}, headers=api_headers)

    first = client.get(f'/api/topic_lists/{list_id}/next_topic', headers=api_headers)
    assert first.status_code == 200

    second = client.get(f'/api/topic_lists/{list_id}/next_topic', headers=api_headers)
    assert second.status_code == 404


def test_deactivate_topic_endpoint(client, api_headers):
    create_resp = client.post('/api/topic_lists', json={'name': 'Animals'}, headers=api_headers)
    list_id = create_resp.get_json()['id']
    add_resp = client.post(
        f'/api/topic_lists/{list_id}/topics', json={'text': 'Lions'}, headers=api_headers
    )
    topic_id = add_resp.get_json()['id']

    resp = client.post(f'/api/topics/{topic_id}/deactivate', headers=api_headers)
    assert resp.status_code == 200
    assert resp.get_json()['active'] is False


def test_admin_index_lists_topic_lists(client, api_headers):
    client.post('/api/topic_lists', json={'name': 'Animals'}, headers=api_headers)
    resp = client.get('/admin/')
    assert resp.status_code == 200
    assert b'Animals' in resp.data


def test_admin_list_detail_shows_topics(client, api_headers):
    create_resp = client.post('/api/topic_lists', json={'name': 'Animals'}, headers=api_headers)
    list_id = create_resp.get_json()['id']
    client.post(f'/api/topic_lists/{list_id}/topics', json={'text': 'Lions'}, headers=api_headers)

    resp = client.get(f'/admin/lists/{list_id}')
    assert resp.status_code == 200
    assert b'Lions' in resp.data


def test_admin_suggest_page_renders_with_no_llm_configured(client, api_headers):
    create_resp = client.post('/api/topic_lists', json={'name': 'Animals'}, headers=api_headers)
    list_id = create_resp.get_json()['id']

    resp = client.get(f'/admin/lists/{list_id}/suggest')
    assert resp.status_code == 200
    assert b'No suggestions available' in resp.data

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_create_chat(client: AsyncClient, auth_header, test_user2):
    response = await client.post(
        "/api/v1/chats/",
        headers=auth_header,
        json={"name": "Test Chat", "member_ids": [test_user2.id]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Chat"
    assert len(data["members"]) == 2


async def test_create_chat_with_invalid_member(client: AsyncClient, auth_header):
    response = await client.post(
        "/api/v1/chats/",
        headers=auth_header,
        json={"name": "Invalid Member Chat", "member_ids": [99999]}  # Non-existent user ID
    )
    assert response.status_code == 404


async def test_get_chats(client: AsyncClient, auth_header):
    # Create multiple chats
    await client.post("/api/v1/chats/", headers=auth_header, json={"name": "Chat 1", "member_ids": []})
    await client.post("/api/v1/chats/", headers=auth_header, json={"name": "Chat 2", "member_ids": []})

    response = await client.get("/api/v1/chats/", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


async def test_get_chats_with_pagination(client: AsyncClient, auth_header):
    # Create multiple chats
    for i in range(5):
        await client.post("/api/v1/chats/", headers=auth_header, json={"name": f"Chat {i}", "member_ids": []})

    response = await client.get("/api/v1/chats/?skip=2&limit=2", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


async def test_get_chats_with_name_filter(client: AsyncClient, auth_header):
    await client.post("/api/v1/chats/", headers=auth_header, json={"name": "Alpha Chat", "member_ids": []})
    await client.post("/api/v1/chats/", headers=auth_header, json={"name": "Beta Chat", "member_ids": []})

    response = await client.get("/api/v1/chats/?name=Alpha", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Alpha Chat"


async def test_start_chat(client: AsyncClient, auth_header, test_user, test_user2):
    response = await client.post(
        "/api/v1/chats/start",
        headers=auth_header,
        json={"other_user_id": test_user2.id}
    )
    assert response.status_code == 200
    data = response.json()
    expected_chat_name = f"Chat between {test_user.username} and {test_user2.username}"
    assert expected_chat_name in data["name"]


async def test_start_chat_with_nonexistent_user(client: AsyncClient, auth_header):
    response = await client.post(
        "/api/v1/chats/start",
        headers=auth_header,
        json={"other_user_id": 99999}
    )
    assert response.status_code == 404


async def test_get_chat_by_id(client: AsyncClient, auth_header):
    create_response = await client.post(
        "/api/v1/chats/",
        headers=auth_header,
        json={"name": "Test Chat", "member_ids": []}
    )
    chat_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/chats/{chat_id}", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == chat_id
    assert data["name"] == "Test Chat"


async def test_get_nonexistent_chat(client: AsyncClient, auth_header):
    response = await client.get("/api/v1/chats/99999", headers=auth_header)
    assert response.status_code == 404


async def test_update_chat(client: AsyncClient, auth_header):
    create_response = await client.post(
        "/api/v1/chats/",
        headers=auth_header,
        json={"name": "Original Chat", "member_ids": []}
    )
    chat_id = create_response.json()["id"]

    update_response = await client.put(
        f"/api/v1/chats/{chat_id}",
        headers=auth_header,
        json={"name": "Updated Chat"}
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Updated Chat"


async def test_update_nonexistent_chat(client: AsyncClient, auth_header):
    response = await client.put(
        "/api/v1/chats/99999",
        headers=auth_header,
        json={"name": "Updated Chat"}
    )
    assert response.status_code == 404


async def test_delete_chat(client: AsyncClient, auth_header):
    create_response = await client.post(
        "/api/v1/chats/",
        headers=auth_header,
        json={"name": "Delete Me Chat", "member_ids": []}
    )
    chat_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/chats/{chat_id}", headers=auth_header)
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/chats/{chat_id}", headers=auth_header)
    assert get_response.status_code == 404


async def test_delete_nonexistent_chat(client: AsyncClient, auth_header):
    response = await client.delete("/api/v1/chats/99999", headers=auth_header)
    assert response.status_code == 404


async def test_add_chat_member(client: AsyncClient, auth_header, test_user, test_user2):
    chat_response = await client.post(
        "/api/v1/chats/",
        headers=auth_header,
        json={"name": "Test Chat", "member_ids": [test_user.id]}
    )
    chat_id = chat_response.json()["id"]

    response = await client.post(
        f"/api/v1/chats/{chat_id}/members",
        headers=auth_header,
        json={"user_id": test_user2.id}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["members"]) == 2
    member_ids = [member["id"] for member in data["members"]]
    assert test_user.id in member_ids
    assert test_user2.id in member_ids


async def test_add_nonexistent_member(client: AsyncClient, auth_header, test_user):
    chat_response = await client.post(
        "/api/v1/chats/",
        headers=auth_header,
        json={"name": "Test Chat", "member_ids": [test_user.id]}
    )
    chat_id = chat_response.json()["id"]

    response = await client.post(
        f"/api/v1/chats/{chat_id}/members",
        headers=auth_header,
        json={"user_id": 99999}
    )
    assert response.status_code == 404


async def test_remove_chat_member(client: AsyncClient, auth_header, test_user, test_user2):
    chat_response = await client.post(
        "/api/v1/chats/",
        headers=auth_header,
        json={"name": "Test Chat", "member_ids": [test_user.id, test_user2.id]}
    )
    chat_id = chat_response.json()["id"]

    response = await client.delete(f"/api/v1/chats/{chat_id}/members/{test_user2.id}", headers=auth_header)
    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/chats/{chat_id}", headers=auth_header)
    assert get_response.status_code == 200
    data = get_response.json()
    member_ids = [member["id"] for member in data["members"]]
    assert test_user2.id not in member_ids


async def test_remove_nonexistent_member(client: AsyncClient, auth_header, test_user):
    chat_response = await client.post(
        "/api/v1/chats/",
        headers=auth_header,
        json={"name": "Test Chat", "member_ids": [test_user.id]}
    )
    chat_id = chat_response.json()["id"]

    response = await client.delete(f"/api/v1/chats/{chat_id}/members/99999", headers=auth_header)
    assert response.status_code == 404


async def test_get_chat_members(client: AsyncClient, auth_header, test_user, test_user2):
    chat_response = await client.post(
        "/api/v1/chats/",
        headers=auth_header,
        json={"name": "Test Chat", "member_ids": [test_user.id, test_user2.id]}
    )
    chat_id = chat_response.json()["id"]

    response = await client.get(f"/api/v1/chats/{chat_id}/members", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    member_ids = [member["id"] for member in data]
    assert test_user.id in member_ids
    assert test_user2.id in member_ids


async def test_get_unread_messages_count(client: AsyncClient, auth_header, test_user):
    chat_response = await client.post(
        "/api/v1/chats/",
        headers=auth_header,
        json={"name": "Test Chat", "member_ids": [test_user.id]}
    )
    chat_id = chat_response.json()["id"]

    response = await client.get(f"/api/v1/chats/{chat_id}/unread_count", headers=auth_header)
    assert response.status_code == 200
    assert isinstance(response.json(), int)


async def test_get_unread_messages_count_nonexistent_chat(client: AsyncClient, auth_header):
    response = await client.get("/api/v1/chats/99999/unread_count", headers=auth_header)
    assert response.status_code == 404

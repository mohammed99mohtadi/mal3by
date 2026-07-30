import pytest
from app.models.match import MatchJoinPolicy, MatchJoinRequestStatus, ParticipantStatus
from tests.test_matches import register_user, setup_match


def get_auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def setup_api_match_and_users(client, db_session, suffix=""):
    _, creator_token, _, _, match_dict = setup_match(client, db_session, suffix=f"_api{suffix}")
    headers_creator = get_auth_headers(creator_token)

    # Set match policy to APPROVAL_REQUIRED
    res = client.patch(
        f"/api/v1/matches/{match_dict['id']}",
        json={"join_policy": MatchJoinPolicy.APPROVAL_REQUIRED.value},
        headers=headers_creator,
    )
    assert res.status_code == 200

    user1_id, token_p1 = register_user(client, db_session, f"api_player1{suffix}@example.com")
    user2_id, token_p2 = register_user(client, db_session, f"api_player2{suffix}@example.com")
    headers_p1 = get_auth_headers(token_p1)
    headers_p2 = get_auth_headers(token_p2)

    user1 = {"id": user1_id, "full_name": "Match User"}
    user2 = {"id": user2_id, "full_name": "Match User"}

    return match_dict["id"], headers_creator, headers_p1, headers_p2, user1, user2


def test_api_create_join_request_success(client, db_session):
    match_id, _, headers_p1, _, user1, _ = setup_api_match_and_users(client, db_session, suffix="_create_ok")

    res = client.post(
        f"/api/v1/matches/{match_id}/join-requests",
        json={},
        headers=headers_p1,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["id"] is not None
    assert data["match_id"] == match_id
    assert data["user_id"] == user1["id"]
    assert data["status"] == MatchJoinRequestStatus.PENDING.value
    assert data["requested_position_code"] is None
    assert "email" not in data.get("requester", {})
    assert data.get("requester", {}).get("full_name") == user1["full_name"]


def test_api_create_join_request_unauthenticated(client, db_session):
    match_id, _, _, _, _, _ = setup_api_match_and_users(client, db_session, suffix="_create_401")

    res = client.post(
        f"/api/v1/matches/{match_id}/join-requests",
        json={},
    )
    assert res.status_code == 401


def test_api_create_join_request_invalid_body(client, db_session):
    match_id, _, headers_p1, _, _, _ = setup_api_match_and_users(client, db_session, suffix="_create_422")

    res = client.post(
        f"/api/v1/matches/{match_id}/join-requests",
        json={"position_code": "a" * 101},  # exceeds max_length=100
        headers=headers_p1,
    )
    assert res.status_code == 422


def test_api_create_join_request_conflict_propagates(client, db_session):
    match_id, headers_creator, headers_p1, _, _, _ = setup_api_match_and_users(client, db_session, suffix="_create_409")

    # Creator self-join attempt should return 409 Conflict
    res = client.post(
        f"/api/v1/matches/{match_id}/join-requests",
        json={},
        headers=headers_creator,
    )
    assert res.status_code == 409
    assert res.json()["detail"] == "Match creator cannot create a join request for their own match"


def test_api_withdraw_join_request_success(client, db_session):
    match_id, _, headers_p1, _, _, _ = setup_api_match_and_users(client, db_session, suffix="_withdraw_ok")

    create_res = client.post(
        f"/api/v1/matches/{match_id}/join-requests",
        json={},
        headers=headers_p1,
    )
    req_id = create_res.json()["id"]

    res = client.post(
        f"/api/v1/matches/{match_id}/join-requests/{req_id}/withdraw",
        headers=headers_p1,
    )
    assert res.status_code == 200
    assert res.json()["status"] == MatchJoinRequestStatus.WITHDRAWN.value


def test_api_withdraw_join_request_mismatched_match_id(client, db_session):
    match_id1, _, headers_p1, _, _, _ = setup_api_match_and_users(client, db_session, suffix="_withdraw_mismatch1")
    match_id2, _, _, _, _, _ = setup_api_match_and_users(client, db_session, suffix="_withdraw_mismatch2")

    create_res = client.post(
        f"/api/v1/matches/{match_id1}/join-requests",
        json={},
        headers=headers_p1,
    )
    req_id = create_res.json()["id"]

    # Try withdrawing via wrong match_id2
    res = client.post(
        f"/api/v1/matches/{match_id2}/join-requests/{req_id}/withdraw",
        headers=headers_p1,
    )
    assert res.status_code == 409
    assert res.json()["detail"] == "Join request does not match the target match"


def test_api_withdraw_join_request_non_owner(client, db_session):
    match_id, _, headers_p1, headers_p2, _, _ = setup_api_match_and_users(client, db_session, suffix="_withdraw_403")

    create_res = client.post(
        f"/api/v1/matches/{match_id}/join-requests",
        json={},
        headers=headers_p1,
    )
    req_id = create_res.json()["id"]

    res = client.post(
        f"/api/v1/matches/{match_id}/join-requests/{req_id}/withdraw",
        headers=headers_p2,
    )
    assert res.status_code == 403


def test_api_approve_join_request_manager_success(client, db_session):
    match_id, headers_creator, headers_p1, _, user1, _ = setup_api_match_and_users(client, db_session, suffix="_app_ok")

    create_res = client.post(
        f"/api/v1/matches/{match_id}/join-requests",
        json={},
        headers=headers_p1,
    )
    req_id = create_res.json()["id"]

    res = client.post(
        f"/api/v1/matches/{match_id}/join-requests/{req_id}/approve",
        headers=headers_creator,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == MatchJoinRequestStatus.APPROVED.value
    assert data["reviewed_by_user_id"] is not None


def test_api_approve_join_request_mismatched_match_id(client, db_session):
    match_id1, headers_creator1, headers_p1, _, _, _ = setup_api_match_and_users(client, db_session, suffix="_app_mism1")
    match_id2, _, _, _, _, _ = setup_api_match_and_users(client, db_session, suffix="_app_mism2")

    create_res = client.post(
        f"/api/v1/matches/{match_id1}/join-requests",
        json={},
        headers=headers_p1,
    )
    req_id = create_res.json()["id"]

    res = client.post(
        f"/api/v1/matches/{match_id2}/join-requests/{req_id}/approve",
        headers=headers_creator1,
    )
    assert res.status_code == 409
    assert res.json()["detail"] == "Join request does not match the target match"


def test_api_approve_join_request_non_manager(client, db_session):
    match_id, _, headers_p1, headers_p2, _, _ = setup_api_match_and_users(client, db_session, suffix="_app_403")

    create_res = client.post(
        f"/api/v1/matches/{match_id}/join-requests",
        json={},
        headers=headers_p1,
    )
    req_id = create_res.json()["id"]

    res = client.post(
        f"/api/v1/matches/{match_id}/join-requests/{req_id}/approve",
        headers=headers_p2,
    )
    assert res.status_code == 403


def test_api_reject_join_request_manager_success(client, db_session):
    match_id, headers_creator, headers_p1, _, _, _ = setup_api_match_and_users(client, db_session, suffix="_rej_ok")

    create_res = client.post(
        f"/api/v1/matches/{match_id}/join-requests",
        json={},
        headers=headers_p1,
    )
    req_id = create_res.json()["id"]

    res = client.post(
        f"/api/v1/matches/{match_id}/join-requests/{req_id}/reject",
        headers=headers_creator,
    )
    assert res.status_code == 200
    assert res.json()["status"] == MatchJoinRequestStatus.REJECTED.value


def test_api_reject_join_request_mismatched_match_id(client, db_session):
    match_id1, headers_creator1, headers_p1, _, _, _ = setup_api_match_and_users(client, db_session, suffix="_rej_mism1")
    match_id2, _, _, _, _, _ = setup_api_match_and_users(client, db_session, suffix="_rej_mism2")

    create_res = client.post(
        f"/api/v1/matches/{match_id1}/join-requests",
        json={},
        headers=headers_p1,
    )
    req_id = create_res.json()["id"]

    res = client.post(
        f"/api/v1/matches/{match_id2}/join-requests/{req_id}/reject",
        headers=headers_creator1,
    )
    assert res.status_code == 409
    assert res.json()["detail"] == "Join request does not match the target match"


def test_api_reject_join_request_non_manager(client, db_session):
    match_id, _, headers_p1, headers_p2, _, _ = setup_api_match_and_users(client, db_session, suffix="_rej_403")

    create_res = client.post(
        f"/api/v1/matches/{match_id}/join-requests",
        json={},
        headers=headers_p1,
    )
    req_id = create_res.json()["id"]

    res = client.post(
        f"/api/v1/matches/{match_id}/join-requests/{req_id}/reject",
        headers=headers_p2,
    )
    assert res.status_code == 403


def test_api_list_match_join_requests_manager_success(client, db_session):
    match_id, headers_creator, headers_p1, headers_p2, _, _ = setup_api_match_and_users(client, db_session, suffix="_list_match")

    client.post(f"/api/v1/matches/{match_id}/join-requests", json={}, headers=headers_p1)
    client.post(f"/api/v1/matches/{match_id}/join-requests", json={}, headers=headers_p2)

    res = client.get(
        f"/api/v1/matches/{match_id}/join-requests",
        headers=headers_creator,
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2


def test_api_list_match_join_requests_non_manager_returns_403(client, db_session):
    match_id, _, headers_p1, _, _, _ = setup_api_match_and_users(client, db_session, suffix="_list_match_403")

    res = client.get(
        f"/api/v1/matches/{match_id}/join-requests",
        headers=headers_p1,
    )
    assert res.status_code == 403


def test_api_list_my_join_requests_route_ordering_and_filtering(client, db_session):
    match_id, _, headers_p1, _, _, _ = setup_api_match_and_users(client, db_session, suffix="_me_requests")

    client.post(f"/api/v1/matches/{match_id}/join-requests", json={}, headers=headers_p1)

    # Prove /matches/me/join-requests resolves cleanly to list_user_join_requests endpoint and is NOT captured by /{match_id}
    res = client.get(
        "/api/v1/matches/me/join-requests",
        headers=headers_p1,
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["match_id"] == match_id
    assert "email" not in data[0].get("requester", {})

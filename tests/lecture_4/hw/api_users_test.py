from datetime import datetime
import pytest
from http import HTTPStatus

from faker import Faker
from fastapi.testclient import TestClient

from lecture_4.demo_service.core.users import UserService, UserRole, password_is_longer_than_8
from lecture_4.demo_service.api.main import create_app

# Какими функциями обладает сервис
# 1. регистрация пользователей /user-register
# params: RegisterUserRequest
# return UserResponse
# может быть уже зарегистрирован
# 
# 2. получаем информацию о пользователе /user-get
# params: принимает id или username (одно из двух)
# 
# 3. даем пользователю права админа /user-promote
# 

faker = Faker()

@pytest.fixture(scope="session")
def client():
    app = create_app()
    app.dependency_overrides['user_service'] = UserService([password_is_longer_than_8])
    with TestClient(app) as client:
        yield client


def valid_user_data():
    return {
        "username": "vader",
        "name": "darth vader",
        "birthdate": datetime(2000, 1, 1).isoformat(),
        "password": "father-pass-123"
    }

def invalid_password_user_data():
    return {
        "username": faker.user_name(),
        "name": faker.name(),
        "birthdate": faker.date_of_birth().isoformat(),
        "password": faker.password(length=5)
    }

def valid_admin_data():
    return {
        "username": "admin",
        "name": "admin",
        "birthdate": datetime.fromtimestamp(0.0).isoformat(),
        "role": UserRole.ADMIN,
        "password": "superSecretAdminPassword123",
    }


@pytest.mark.parametrize(
    ("user_info", "expected_status"),
    [
        (valid_user_data(), HTTPStatus.OK),
        (valid_user_data(), HTTPStatus.BAD_REQUEST),
        (
            {key: value for key, value in valid_user_data().items() if key != "password"}, 
            HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
        (
            {key: value for key, value in valid_user_data().items() if key != "username"},
            HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
        (invalid_password_user_data(), HTTPStatus.BAD_REQUEST)
    ]
)
@pytest.mark.asyncio
async def test_register_user(client, request, user_info, expected_status):
    response = client.post("/user-register", json=user_info)

    assert response.status_code == expected_status

    if expected_status == HTTPStatus.OK:
        data = response.json()
        assert data["username"] == user_info["username"]
        assert data["name"] == user_info["name"]
        assert data["birthdate"] == user_info["birthdate"]
        assert data["role"].lower() == UserRole.USER


@pytest.mark.parametrize(
    ("params", "expected_status", "expected_user"),
    [
        ({"id": 1}, HTTPStatus.OK, valid_admin_data()),
        ({"username": "vader"}, HTTPStatus.OK, valid_user_data()),
        ({"id": 777}, HTTPStatus.NOT_FOUND, {}),
        ({"username": "non_existent_user"}, HTTPStatus.NOT_FOUND, {}),
        ({"id": 2, "username": "vader"}, HTTPStatus.BAD_REQUEST, {}),
        ({}, HTTPStatus.BAD_REQUEST, {}),
    ]
)
@pytest.mark.asyncio
async def test_get_user(client, params, expected_status, expected_user):
    response = client.post("/user-get", params=params, auth=("admin", "superSecretAdminPassword123"))
    
    assert response.status_code == expected_status

    if expected_status == HTTPStatus.OK:
        data = response.json()
        assert data["username"] == expected_user["username"]
        assert data["name"] == expected_user["name"]
        assert data["birthdate"] == expected_user["birthdate"]


@pytest.mark.parametrize(
    ("params", "auth", "status_code"),
    [
        ({}, None, HTTPStatus.UNAUTHORIZED),
        ({"id": 1}, ("admin", "superSecretAdminPassword123"), HTTPStatus.OK),
        ({"id": 3}, ("admin", "superSecretAdminPassword123"), HTTPStatus.BAD_REQUEST),
        ({"id": 2}, ("vader", "father-pass-123"), HTTPStatus.FORBIDDEN),
        ({"id": 2}, ("admin", "superSecretAdminPassword123"), HTTPStatus.OK),
        ({"id": 2}, ("admin", "superSecretAdminPassword1"), HTTPStatus.UNAUTHORIZED),
    ]
)
@pytest.mark.asyncio
async def test_promote_user(client, params, auth, status_code):
    response = client.post("/user-promote", params=params, auth=auth)
    assert response.status_code == status_code
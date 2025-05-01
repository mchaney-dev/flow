import pytest
from unittest.mock import MagicMock, patch
from main import get_users, delete_users, register_user, login_user, get_user, update_user, delete_user
import bcrypt
import json

@patch("main.get_users_collection")
def test_register_user_success(mock_users_collection):
    user = {
        "email": "user@example.com",
        "password": "Password123!",
        "type": "user"
    }
    
    expected = (
        json.dumps({
            "message": "Created",
            "data": ""
        }),
        201,
        {
            "Content-Type": "application/json"
        }
    )

    # mock users collection
    mock_users = MagicMock()
    mock_users_collection.return_value = mock_users

    # mock request data
    data = user

    response = register_user(data)

    assert response == expected

@patch("main.get_users_collection")
def test_register_user_existing_email_fail(mock_users_collection):
    user = {
        "email": "user@example.com",
        "password": "Password123!",
        "type": "user"
    }
    
    expected = (
        json.dumps({
            "message": "Conflict",
            "data": ""
        }),
        409,
        {
            "Content-Type": "application/json"
        }
    )

    # mock firestore document stream result
    mock_existing_user = MagicMock()
    mock_existing_user.to_dict.return_value = user

    # mock collection
    mock_users = MagicMock()
    
    # when register_user calls .where(...).limit(1).stream(), return a non-empty list
    mock_users.where.return_value.limit.return_value.stream.return_value = [mock_existing_user]
    mock_users_collection.return_value = mock_users

    # mock request data
    data = user

    response = register_user(data)

    assert response == expected

@pytest.mark.parametrize("invalid_data", [
    {"email": "", "password": "Password123!", "type": "user"},
    {"email": "exampledotcom", "password": "Password123!", "type": "user"},
    {"password": "Password123!", "type": "user"},
    {"email": None, "password": "Password123!", "type": "user"}
])
@patch("main.get_users_collection")
def test_register_user_invalid_email_fail(mock_users_collection, invalid_data):
    expected = (
        json.dumps({
            "message": "Bad Request",
            "data": ""
        }),
        400,
        {
            "Content-Type": "application/json"
        }
    )

    # mock users collection
    mock_users = MagicMock()
    mock_users_collection.return_value = mock_users

    response = register_user(invalid_data)

    assert response == expected

@pytest.mark.parametrize("invalid_data", [
    {"email": "email@example.com", "password": "", "type": "user"},
    {"email": "email@example.com", "password": "pw", "type": "user"},
    {"email": "email@example.com", "type": "user"},
    {"email": "email@example.com", "password": None, "type": "user"}
])
@patch("main.get_users_collection")
def test_register_user_invalid_password_fail(mock_users_collection, invalid_data):
    expected = (
        json.dumps({
            "message": "Bad Request",
            "data": ""
        }),
        400,
        {
            "Content-Type": "application/json"
        }
    )

    # mock users collection
    mock_users = MagicMock()
    mock_users_collection.return_value = mock_users

    response = register_user(invalid_data)

    assert response == expected

@pytest.mark.parametrize("invalid_data", [
    {"email": "email@example.com", "password": "Password123!", "type": ""},
    {"email": "email@example.com", "password": "Password123!", "type": "account"},
    {"email": "email@example.com", "password": "Password123!", "type": None},
    {"email": "email@example.com", "password": "Password123!"}
])
@patch("main.get_users_collection")
def test_register_user_invalid_type_fail(mock_users_collection, invalid_data):
    expected = (
        json.dumps({
            "message": "Bad Request",
            "data": ""
        }),
        400,
        {
            "Content-Type": "application/json"
        }
    )

    # mock users collection
    mock_users = MagicMock()
    mock_users_collection.return_value = mock_users

    response = register_user(invalid_data)

    assert response == expected
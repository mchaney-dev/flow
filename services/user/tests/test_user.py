import pytest
from unittest.mock import MagicMock, patch
from main import get_users, delete_users, register_user, login_user, get_user, update_user, delete_user
import bcrypt
import json

# get_users tests
@patch("main.get_users_collection")
def test_get_users_success(mock_users_collection):
    # mock doc for a sample user
    user = {
        "id": "1",
        "email": "email@example.com",
        "password": "Password123!",
        "type": "user"
    }
    mock_user_doc = MagicMock()
    mock_user_doc.to_dict.return_value = user

    expected = (
        json.dumps({
            "message": "OK",
            "data": {
                "users": [user],
                "nextPageToken": ""
            }
        }),
        200,
        {
            "Content-Type": "application/json"
        }
    )

    # mock query behavior
    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_user_doc]
    mock_users_collection.return_value = mock_query
    
    response = get_users()

    assert response == expected

@patch("main.get_users_collection")
def test_get_users_invalid_type_fail(mock_users_collection):
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

    response = get_users({"type": "guest"})

    assert response == expected

@pytest.mark.parametrize("invalid_data", [
    {"limit": "abc"},
    {"limit": None},
    {"limit": 5.5}
])
@patch("main.get_users_collection")
def test_get_users_invalid_limit_fail(mock_users_collection, invalid_data):
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

    response = get_users(invalid_data)

    assert response == expected

@pytest.mark.parametrize("invalid_data", [
    {"start_after": None},
    {"start_after": "not_base64"}
])
@patch("main.get_users_collection")
def test_get_users_invalid_start_after_fail(mock_users_collection, invalid_data):
    expected = (
        json.dumps({
            "message": "Internal Server Error",
            "data": ""
        }),
        500,
        {
            "Content-Type": "application/json"
        }
    )

    response = get_users(invalid_data)

    assert response == expected

# delete_users tests
@patch("main.get_db")
@patch("main.get_users_collection")
def test_delete_users_success(mock_users_collection, mock_get_db):
    # mock doc for a sample user
    user = {
        "id": "1",
        "email": "email@example.com",
        "password": "Password123!",
        "type": "user"
    }
    mock_user_doc = MagicMock()
    mock_user_doc.to_dict.return_value = user
    mock_user_doc.id = "1"

    # mock query behavior
    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_user_doc]
    mock_users_collection.return_value = mock_query

    # mock db and batch
    mock_batch = MagicMock()
    mock_db = MagicMock()
    mock_db.batch.return_value = mock_batch
    mock_get_db.return_value = mock_db

    expected = (
        json.dumps({
            "message": "OK",
            "data": {
                "deletedUserCount": 1,
                "deletedUserIds": ["1"]
            }
        }),
        200,
        {
            "Content-Type": "application/json"
        }
    )
    
    response = delete_users()

    assert response == expected

@patch("main.get_db")
@patch("main.get_users_collection")
def test_delete_users_invalid_type_fail(mock_users_collection, mock_get_db):
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
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

    response = delete_users({"type": "guest"})

    assert response == expected

# register_user tests
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

# login_user tests
@patch("main.get_users_collection")
def test_login_user_success(mock_users_collection):
    user = {
        "email": "email@example.com",
        "password": "Password123!"
    }

    expected = (
        json.dumps({
            "message": "OK",
            "data": ""
        }),
        200,
        {
            "Content-Type": "application/json"
        }
    )

    # mock user doc with hashed password
    hashed_pw = bcrypt.hashpw("Password123!".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    mock_user_doc = MagicMock()
    mock_user_doc.to_dict.return_value = {
        "email": "email@example.com",
        "password": hashed_pw
    }

    # mock query
    mock_query = MagicMock()
    mock_query.where.return_value.limit.return_value.stream.return_value = [mock_user_doc]
    mock_users_collection.return_value = mock_query

    response = login_user(user)
    
    assert response == expected

@pytest.mark.parametrize("invalid_data", [
    {"email": "", "password": "Password123!"},
    {"password": "Password123!"},
    {"email": None, "password": "Password123!"}
])
@patch("main.get_users_collection")
def test_login_user_invalid_email_fail(mock_users_collection, invalid_data):
    expected = (
        json.dumps({
            "message": "Internal Server Error",
            "data": ""
        }),
        500,
        {
            "Content-Type": "application/json"
        }
    )

    # mock users collection
    mock_users = MagicMock()
    mock_users_collection.return_value = mock_users

    response = login_user(invalid_data)

    assert response == expected

@pytest.mark.parametrize("invalid_data", [
    {"email": "email@example.com", "password": ""},
    {"email": "email@example.com"},
    {"email": "email@example.com", "password": None}
])
@patch("main.get_users_collection")
def test_login_user_invalid_password_fail(mock_users_collection, invalid_data):
    expected = (
        json.dumps({
            "message": "Internal Server Error",
            "data": ""
        }),
        500,
        {
            "Content-Type": "application/json"
        }
    )

    # mock users collection
    mock_users = MagicMock()
    mock_users_collection.return_value = mock_users

    response = login_user(invalid_data)

    assert response == expected

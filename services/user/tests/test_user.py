import pytest
from unittest.mock import MagicMock, patch
from main import get_users, delete_users, register_user, login_user, get_user, update_user, delete_user, update_password
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

# get_user tests
@patch("main.get_users_collection")
def test_get_user_success(mock_users_collection):
    user_id = "1"
    
    user = {
        "id": user_id,
        "email": "user@example.com",
        "password": "Password123!",
        "type": "user"
    }

    mock_user_doc = MagicMock()
    mock_user_doc.to_dict.return_value = user

    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_user_doc]

    mock_collection = MagicMock()
    mock_collection.where.return_value = mock_query

    mock_users_collection.return_value = mock_collection

    expected = (
        json.dumps({
            "message": "OK",
            "data": {
                "user": user
            }
        }),
        200,
        {
            "Content-Type": "application/json"
        }
    )
    
    response = get_user(user_id)

    assert response == expected

@patch("main.get_users_collection")
@pytest.mark.parametrize("invalid_data", ["", 0, None])
def test_get_user_invalid_id_fail(mock_users_collection, invalid_data):
    mock_query = MagicMock()
    mock_query.stream.return_value = []

    mock_collection = MagicMock()
    mock_collection.where.return_value = mock_query

    mock_users_collection.return_value = mock_collection
    
    expected = (
        json.dumps({
            "message": "Not Found",
            "data": ""
        }),
        404,
        {
            "Content-Type": "application/json"
        }
    )

    response = get_user(invalid_data)

    assert response == expected

# update_user tests
@patch("main.get_db")
@patch("main.get_users_collection")
def test_update_user_success(mock_users_collection, mock_get_db):
    user_id = "1"

    user = {
        "id": user_id,
        "email": "user@example.com",
        "type": "user"
    }

    mock_user_doc = MagicMock()
    mock_user_doc.id = "some_id"
    mock_user_doc.to_dict.return_value = user

    # mock query
    mock_query = MagicMock()
    mock_query.where.return_value.limit.return_value.stream.return_value = [mock_user_doc]
    mock_users_collection.return_value = mock_query

    mock_user_doc_ref = MagicMock()
    mock_collection = MagicMock()
    mock_collection.return_value = mock_user_doc_ref

    mock_db = MagicMock()
    mock_db.collection.return_value = mock_collection
    mock_get_db.return_value = mock_db

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

    response = update_user(user_id, user)

    assert response == expected

@patch("main.get_db")
@patch("main.get_users_collection")
@pytest.mark.parametrize("invalid_data", ["", 0, None])
def test_update_user_invalid_id_fail(mock_users_collection, mock_get_db, invalid_data):
    user = {
        "email": "user@example.com",
        "type": "user"
    }

    mock_user_doc = MagicMock()

    # mock query
    mock_query = MagicMock()
    mock_query.where.return_value.stream.return_value = [mock_user_doc]
    mock_users_collection.return_value = mock_query

    mock_get_db.return_value = MagicMock()

    expected = (
        json.dumps({
            "message": "Not Found",
            "data": ""
        }),
        404,
        {
            "Content-Type": "application/json"
        }
    )

    response = update_user(invalid_data, user)

    assert response == expected

@patch("main.get_db")
@patch("main.get_users_collection")
@pytest.mark.parametrize("invalid_data", [0, None, ""])
def test_update_user_invalid_email_fail(mock_users_collection, mock_get_db, invalid_data):
    user_id = "1"
    
    mock_user_doc = MagicMock()

    # mock query
    mock_query = MagicMock()
    mock_query.where.return_value.stream.return_value = [mock_user_doc]
    mock_users_collection.return_value = mock_query

    mock_user_doc_ref = MagicMock()
    mock_collection = MagicMock()
    mock_collection.return_value = mock_user_doc_ref

    mock_db = MagicMock()
    mock_db.collection.return_value = mock_collection
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

    response = update_user(user_id, {"email": invalid_data})

    assert response == expected

@patch("main.get_db")
@patch("main.get_users_collection")
@pytest.mark.parametrize("invalid_data", [0, None, ""])
def test_update_user_password_fail(mock_users_collection, mock_get_db, invalid_data):
    user_id = "1"
    
    mock_user_doc = MagicMock()

    # mock query
    mock_query = MagicMock()
    mock_query.where.return_value.stream.return_value = [mock_user_doc]
    mock_users_collection.return_value = mock_query

    mock_user_doc_ref = MagicMock()
    mock_collection = MagicMock()
    mock_collection.return_value = mock_user_doc_ref

    mock_db = MagicMock()
    mock_db.collection.return_value = mock_collection
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

    response = update_user(user_id, {"password": invalid_data})

    assert response == expected

@patch("main.get_db")
@patch("main.get_users_collection")
@pytest.mark.parametrize("invalid_data", [0, None, "", "guest"])
def test_update_user_invalid_type_fail(mock_users_collection, mock_get_db, invalid_data):
    user_id = "1"
    
    mock_user_doc = MagicMock()

    # mock query
    mock_query = MagicMock()
    mock_query.where.return_value.stream.return_value = [mock_user_doc]
    mock_users_collection.return_value = mock_query

    mock_user_doc_ref = MagicMock()
    mock_collection = MagicMock()
    mock_collection.return_value = mock_user_doc_ref

    mock_db = MagicMock()
    mock_db.collection.return_value = mock_collection
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

    response = update_user(user_id, {"type": invalid_data})

    assert response == expected

# delete_user tests
@patch("main.get_users_collection")
def test_delete_user_success(mock_users_collection):
    user_id = "1"
    
    mock_doc_ref = MagicMock()
    mock_doc = MagicMock()
    mock_doc.reference = mock_doc_ref

    mock_query = MagicMock()
    mock_query.where.return_value.stream.return_value = [mock_doc]
    mock_users_collection.return_value = mock_query

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

    response = delete_user(user_id)

    assert response == expected

@patch("main.get_users_collection")
@pytest.mark.parametrize("invalid_data", [0, None, ""])
def test_delete_user_invalid_id_fail(mock_users_collection, invalid_data):
    mock_query = MagicMock()
    mock_query.stream.return_value = []

    mock_collection = MagicMock()
    mock_collection.where.return_value = mock_query

    mock_users_collection.return_value = mock_collection
    
    expected = (
        json.dumps({
            "message": "Not Found",
            "data": ""
        }),
        404,
        {
            "Content-Type": "application/json"
        }
    )

    response = delete_user(invalid_data)

    assert response == expected

# update_password tests
@patch("main.get_db")
@patch("main.get_users_collection")
def test_update_password_success(mock_users_collection, mock_get_db):
    user_id = "1"
    prev_password = "Password123!"
    new_password = "Password1234!"

    # hash prev_password
    hashed_pw = bcrypt.hashpw(prev_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    mock_user_doc = MagicMock()
    mock_user_doc.id = "mock_id"
    mock_user_doc.to_dict.return_value = {
        "id": user_id,
        "password": hashed_pw
    }

    mock_query = MagicMock()
    mock_query.where.return_value.limit.return_value.stream.return_value = [mock_user_doc]
    mock_users_collection.return_value = mock_query

    mock_user_doc_ref = MagicMock()
    mock_collection = MagicMock()
    mock_collection.return_value.document.return_value = mock_user_doc_ref

    mock_db = MagicMock()
    mock_db.collection.return_value = mock_collection
    mock_get_db.return_value = mock_db

    user_data = {
        "id": user_id,
        "prevPassword": prev_password,
        "newPassword": new_password
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

    response = update_password(user_id, user_data)

    assert response == expected

@patch("main.get_db")
@patch("main.get_users_collection")
@pytest.mark.parametrize("invalid_data", [0, None, "", "Password123!"])
def test_update_password_invalid_password_fail(mock_users_collection, mock_get_db, invalid_data):
    user_id = "1"
    prev_password = "Password123!"

    # hash prev_password
    hashed_pw = bcrypt.hashpw(prev_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    mock_user_doc = MagicMock()
    mock_user_doc.id = "mock_id"
    mock_user_doc.to_dict.return_value = {
        "id": user_id,
        "password": hashed_pw
    }

    mock_query = MagicMock()
    mock_query.where.return_value.limit.return_value.stream.return_value = [mock_user_doc]
    mock_users_collection.return_value = mock_query

    mock_user_doc_ref = MagicMock()
    mock_collection = MagicMock()
    mock_collection.return_value.document.return_value = mock_user_doc_ref

    mock_db = MagicMock()
    mock_db.collection.return_value = mock_collection
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

    response = update_password(user_id, {"prevPassword": prev_password, "newPassword": invalid_data})

    assert response == expected
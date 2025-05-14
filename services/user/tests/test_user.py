import pytest
from unittest.mock import MagicMock, patch
from main import get_users, delete_users, register_user, login_user, get_user, update_user, delete_user, update_password
import bcrypt
import json

# get_users tests
@patch("main.get_collection")
def test_get_users_success(collection):
    data = {
        "id": "1",
        "email": "email@example.com",
        "password": "Password123!",
        "type": "user"
    }

    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = data

    expected = (
        json.dumps({
            "message": "OK",
            "data": {
                "users": [data],
                "nextPageToken": ""
            }
        }),
        200,
        {
            "Content-Type": "application/json"
        }
    )

    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_doc]
    collection.return_value = mock_query
    
    response = get_users()

    assert response == expected

@pytest.mark.parametrize("invalid_data", ["guest", 0, None, ""])
@patch("main.get_collection")
def test_get_users_invalid_type_fail(collection, invalid_data):
    response = get_users({"type": invalid_data})

    assert "Invalid query parameter 'type'" in response[0]
    assert response[1] == 400

@pytest.mark.parametrize("invalid_data", ["abc", None, 5.5, ""])
@patch("main.get_collection")
def test_get_users_invalid_limit_fail(collection, invalid_data):
    response = get_users({"limit": invalid_data})

    if invalid_data in [None, 5.5]:
        assert "Invalid query parameter 'limit'" in response[0]
        assert response[1] == 400
    else:
        assert "Internal Server Error" in response[0]
        assert response[1] == 500

@pytest.mark.parametrize("invalid_data", [None, "not_base64", ""])
@patch("main.get_collection")
def test_get_users_invalid_start_after_fail(collection, invalid_data):
    response = get_users({"start_after": invalid_data})

    assert "Internal Server Error" in response[0]
    assert response[1] == 500

# delete_users tests
@patch("main.get_db")
@patch("main.get_collection")
def test_delete_users_success(collection, db):
    data = {
        "id": "1",
        "email": "email@example.com",
        "password": "Password123!",
        "type": "user"
    }

    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = data
    mock_doc.id = "1"

    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_doc]
    collection.return_value = mock_query

    mock_batch = MagicMock()
    mock_db = MagicMock()
    mock_db.batch.return_value = mock_batch
    db.return_value = mock_db

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

@pytest.mark.parametrize("invalid_data", ["guest", 0, None, ""])
@patch("main.get_db")
@patch("main.get_collection")
def test_delete_users_invalid_type_fail(collection, db, invalid_data):
    mock_db = MagicMock()
    db.return_value = mock_db
    
    response = delete_users({"type": invalid_data})

    assert "Invalid query parameter 'type'" in response[0]
    assert response[1] == 400

# register_user tests
@patch("main.get_collection")
def test_register_user_success(collection):
    data = {
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

    mock_collection = MagicMock()
    collection.return_value = mock_collection

    response = register_user(data)

    assert response == expected

@patch("main.get_collection")
def test_register_user_existing_email_fail(collection):
    data = {
        "email": "user@example.com",
        "password": "Password123!",
        "type": "user"
    }

    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = data

    mock_collection = MagicMock()
    
    mock_collection.where.return_value.limit.return_value.stream.return_value = [mock_doc]
    collection.return_value = mock_collection

    response = register_user(data)

    assert "Invalid field 'email'" in response[0]
    assert response[1] == 409

@pytest.mark.parametrize("invalid_data", ["", "exampledotcom", None])
@patch("main.get_collection")
def test_register_user_invalid_email_fail(collection, invalid_data):
    data = {
        "email": invalid_data,
        "password": "Password123!",
        "type": "user"
    }

    mock_collection = MagicMock()
    collection.return_value = mock_collection

    response = register_user(data)

    assert "Invalid field 'email'" in response[0]
    assert response[1] == 400

@pytest.mark.parametrize("invalid_data", ["", "pw", None])
@patch("main.get_collection")
def test_register_user_invalid_password_fail(collection, invalid_data):
    data = {
        "email": "email@example.com",
        "password": invalid_data,
        "type": "user"
    }

    mock_collection = MagicMock()
    collection.return_value = mock_collection

    response = register_user(data)

    assert "Invalid field 'password'" in response[0]
    assert response[1] == 400

@pytest.mark.parametrize("invalid_data", ["", "account", None])
@patch("main.get_collection")
def test_register_user_invalid_type_fail(collection, invalid_data):
    data = {
        "email": "email@example.com",
        "password": "Password123!",
        "type": invalid_data
    }

    mock_collection = MagicMock()
    collection.return_value = mock_collection

    response = register_user(data)

    assert "Invalid field 'type'" in response[0]
    assert response[1] == 400

# login_user tests
@patch("main.get_collection")
def test_login_user_success(collection):
    data = {
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

    hashed_pw = bcrypt.hashpw("Password123!".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = {
        "email": "email@example.com",
        "password": hashed_pw
    }

    mock_query = MagicMock()
    mock_query.where.return_value.limit.return_value.stream.return_value = [mock_doc]
    collection.return_value = mock_query

    response = login_user(data)
    
    assert response == expected

@pytest.mark.parametrize("invalid_data", ["", "emaildotcom", None])
@patch("main.get_collection")
def test_login_user_invalid_email_fail(collection, invalid_data):
    data = {
        "email": invalid_data,
        "password": "Password123!",
        "type": "user"
    }

    mock_collection = MagicMock()
    collection.return_value = mock_collection

    response = login_user(data)

    assert "Invalid field 'email'" in response[0]
    assert response[1] == 400

@pytest.mark.parametrize("invalid_data", ["", "pw", None])
@patch("main.get_collection")
def test_login_user_invalid_password_fail(collection, invalid_data):
    data = {
        "email": "email@example.com",
        "password": invalid_data,
        "type": "user"
    }

    mock_collection = MagicMock()
    collection.return_value = mock_collection

    response = login_user(data)

    assert "Invalid field 'password'" in response[0]
    assert response[1] == 400

# get_user tests
@patch("main.get_collection")
def test_get_user_success(collection):
    data = {
        "id": "1",
        "email": "user@example.com",
        "password": "Password123!",
        "type": "user"
    }

    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = data

    mock_query = MagicMock()
    mock_query.where.return_value.limit.return_value.stream.return_value = [mock_doc]
    collection.return_value = mock_query

    expected = (
        json.dumps({
            "message": "OK",
            "data": {
                "user": data
            }
        }),
        200,
        {
            "Content-Type": "application/json"
        }
    )
    
    response = get_user(data["id"])

    assert response == expected

@patch("main.get_collection")
@pytest.mark.parametrize("invalid_data", ["", 0, None])
def test_get_user_invalid_id_fail(collection, invalid_data):
    mock_query = MagicMock()
    mock_query.stream.return_value = []

    mock_collection = MagicMock()
    mock_collection.where.return_value = mock_query

    collection.return_value = mock_collection

    response = get_user(invalid_data)

    if invalid_data == "":
        assert "Required field 'user_id' must not be empty string" in response[0]
        assert response[1] == 400
    else:
        assert "Invalid field 'user_id'" in response[0]
        assert response[1] == 400

# update_user tests
@patch("main.get_db")
@patch("main.get_collection")
def test_update_user_success(collection, db):
    data = {
        "id": "1",
        "type": "admin"
    }

    mock_doc = MagicMock()
    mock_doc.id = data["id"]
    mock_doc.to_dict.return_value = data

    mock_query = MagicMock()
    mock_query.where.return_value.limit.return_value.stream.return_value = [mock_doc]
    collection.return_value = mock_query

    mock_doc_ref = MagicMock()
    mock_collection = MagicMock()
    mock_collection.return_value = mock_doc_ref

    mock_db = MagicMock()
    mock_db.collection.return_value = mock_collection
    db.return_value = mock_db

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

    response = update_user(data["id"], data)

    assert response == expected

@patch("main.get_db")
@patch("main.get_collection")
@pytest.mark.parametrize("invalid_data", ["", "some_id", None])
def test_update_user_invalid_id_fail(collection, db, invalid_data):
    data = {
        "id": invalid_data,
        "type": "admin"
    }

    response = update_user(data["id"], data)

    if invalid_data == "":
        assert "Required field 'user_id' must not be empty string" in response[0]
        assert response[1] == 400
    else:
        assert "Invalid field 'user_id'" in response[0]
        assert response[1] >= 400

@patch("main.get_db")
@patch("main.get_collection")
@pytest.mark.parametrize("invalid_data", [None, "", "emaildotcom"])
def test_update_user_invalid_email_fail(collection, db, invalid_data):
    data = {
        "id": "1",
        "email": invalid_data
    }

    mock_doc = MagicMock()

    mock_query = MagicMock()
    mock_query.where.return_value.limit.return_value.stream.return_value = [mock_doc]
    collection.return_value = mock_query

    db.return_value = MagicMock()

    response = update_user(data["id"], data)

    assert "Invalid field 'email'" in response[0]
    assert response[1] == 400

@patch("main.get_db")
@patch("main.get_collection")
@pytest.mark.parametrize("invalid_data", [0, None, "", "guest"])
def test_update_user_invalid_type_fail(collection, db, invalid_data):
    data = {
        "id": "1",
        "type": invalid_data
    }

    mock_doc = MagicMock()

    mock_query = MagicMock()
    mock_query.where.return_value.limit.return_value.stream.return_value = [mock_doc]
    collection.return_value = mock_query

    db.return_value = MagicMock()

    response = update_user(data["id"], data)

    assert "Invalid field 'type'" in response[0]
    assert response[1] == 400

# delete_user tests
@patch("main.get_collection")
def test_delete_user_success(collection):
    data = {
        "id": "1",
        "email": "user@example.com",
        "password": "Password123!",
        "type": "user"
    }

    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = data

    mock_query = MagicMock()
    mock_query.where.return_value.limit.return_value.stream.return_value = [mock_doc]
    collection.return_value = mock_query

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
    
    response = delete_user(data["id"])

    assert response == expected

@patch("main.get_collection")
@pytest.mark.parametrize("invalid_data", [0, None, ""])
def test_delete_user_invalid_id_fail(collection, invalid_data):
    response = delete_user(invalid_data)

    if invalid_data == "":
        assert "Required field 'user_id' must not be empty string" in response[0]
        assert response[1] == 400
    else:
        assert "Invalid field 'user_id'" in response[0]
        assert response[1] >= 400

# update_password tests
@patch("main.get_db")
@patch("main.get_collection")
def test_update_password_success(collection, db):
    data = {
        "id": "1",
        "prevPassword": "Password123!",
        "newPassword": "Password1234!"
    }

    # hash prevPassword
    hashed_pw = bcrypt.hashpw(data["prevPassword"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = {
        "id": "1",
        "email": "user@example.com",
        "password": hashed_pw,
        "type": "user"
    }

    mock_query = MagicMock()
    mock_query.where.return_value.limit.return_value.stream.return_value = [mock_doc]
    collection.return_value = mock_query

    mock_doc_ref = MagicMock()
    mock_collection = MagicMock()
    mock_collection.return_value.document.return_value = mock_doc_ref

    mock_db = MagicMock()
    mock_db.collection.return_value = mock_collection
    db.return_value = mock_db

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

    response = update_password(data["id"], data)

    assert response == expected

@patch("main.get_db")
@patch("main.get_collection")
@pytest.mark.parametrize("invalid_data", [0, None, "", "pw"])
def test_update_password_invalid_password_fail(collection, db, invalid_data):
    data = {
        "id": "1",
        "prevPassword": "Password123!",
        "newPassword": invalid_data
    }

    # hash prevPassword
    hashed_pw = bcrypt.hashpw(data["prevPassword"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = {
        "id": "1",
        "email": "user@example.com",
        "password": hashed_pw,
        "type": "user"
    }

    mock_query = MagicMock()
    mock_query.where.return_value.limit.return_value.stream.return_value = [mock_doc]
    collection.return_value = mock_query

    mock_doc_ref = MagicMock()
    mock_collection = MagicMock()
    mock_collection.return_value.document.return_value = mock_doc_ref

    mock_db = MagicMock()
    mock_db.collection.return_value = mock_collection
    db.return_value = mock_db

    response = update_password(data["id"], data)

    assert "Invalid field 'newPassword'" in response[0]
    assert response[1] == 400
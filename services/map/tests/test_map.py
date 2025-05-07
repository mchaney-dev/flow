import pytest
from unittest.mock import MagicMock, patch
from main import get_maps, delete_maps, create_map, get_map
import json

# get_maps tests
@patch("main.get_maps_collection")
def test_get_maps_success(mock_maps_collection):
    data = {
        "id": "1",
        "url": "https://example.com"
    }

    mock_map_doc = MagicMock()
    mock_map_doc.to_dict.return_value = data

    expected = (
        json.dumps({
            "message": "OK",
            "data": {
                "maps": [data]
            }
        }),
        200,
        {
            "Content-Type": "application/json"
        }
    )

    # mock query behavior
    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_map_doc]
    mock_maps_collection.return_value = mock_query
    
    response = get_maps()

    assert response == expected

# delete_maps tests
@patch("main.get_db")
@patch("main.get_maps_collection")
def test_delete_maps_success(mock_maps_collection, mock_get_db):
    data = {
        "id": "1",
        "url": "https://example.com"
    }

    mock_map_doc = MagicMock()
    mock_map_doc.to_dict.return_value = data
    mock_map_doc.id = "1"

    # mock query behavior
    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_map_doc]
    mock_maps_collection.return_value = mock_query

    # mock db and batch
    mock_batch = MagicMock()
    mock_db = MagicMock()
    mock_db.batch.return_value = mock_batch
    mock_get_db.return_value = mock_db

    expected = (
        json.dumps({
            "message": "OK",
            "data": {
                "deletedMapCount": 1,
                "deletedMapIds": ["1"]
            }
        }),
        200,
        {
            "Content-Type": "application/json"
        }
    )
    
    response = delete_maps()

    assert response == expected

# create_map tests
@patch("main.get_maps_collection")
def test_create_map_success(mock_maps_collection):
    data = {
        "id": "1",
        "url": "https://example.com"
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

    # mock maps collection
    mock_maps = MagicMock()
    mock_maps_collection.return_value = mock_maps

    response = create_map(data)

    assert response == expected

@pytest.mark.parametrize("invalid_data", [0, None, ""])
@patch("main.get_maps_collection")
def test_create_map_invalid_url_fail(mock_maps_collection, invalid_data):
    data = {
        "id": "1",
        "url": invalid_data
    }

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

    # mock maps collection
    mock_maps = MagicMock()
    mock_maps_collection.return_value = mock_maps

    response = create_map(data)

    assert response == expected

# get_map tests
@patch("main.get_maps_collection")
def test_get_map_success(mock_maps_collection):
    data = {
        "id": "1",
        "url": "https://example.com"
    }

    mock_map_doc = MagicMock()
    mock_map_doc.to_dict.return_value = data

    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_map_doc]

    mock_collection = MagicMock()
    mock_collection.where.return_value = mock_query

    mock_maps_collection.return_value = mock_collection

    expected = (
        json.dumps({
            "message": "OK",
            "data": {
                "map": data
            }
        }),
        200,
        {
            "Content-Type": "application/json"
        }
    )
    
    response = get_map(data["id"])

    assert response == expected

@patch("main.get_maps_collection")
@pytest.mark.parametrize("invalid_data", ["", 0, None])
def test_get_map_invalid_id_fail(mock_maps_collection, invalid_data):
    mock_collection = MagicMock()
    mock_maps_collection.return_value = mock_collection

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

    response = get_map(invalid_data)

    assert response == expected
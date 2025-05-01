import pytest
from unittest.mock import MagicMock, patch
from main import get_routes, delete_routes, create_route, get_route, update_route, delete_route
import json

# get_routes tests
@patch("main.get_routes_collection")
def test_get_routes_success(mock_routes_collection):
    # mock doc for a sample route
    route = {
        "id": "1",
        "name": "Sample Route",
        "stops": [
            "Stop 1",
            "Stop 2",
            "Stop 3"
        ],
        "createdBy": "test_user_id",
        "active": True
    }
    mock_route_doc = MagicMock()
    mock_route_doc.to_dict.return_value = route

    expected = (
        json.dumps({
            "message": "OK",
            "data": {
                "routes": [route]
            }
        }),
        200,
        {
            "Content-Type": "application/json"
        }
    )

    # mock query behavior
    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_route_doc]
    mock_routes_collection.return_value = mock_query
    
    response = get_routes()

    assert response == expected

# delete_routes tests
@patch("main.get_db")
@patch("main.get_routes_collection")
def test_delete_routes_success(mock_routes_collection, mock_get_db):
    # mock doc for a sample route
    route = {
        "id": "1",
        "name": "Sample Route",
        "stops": [
            "Stop 1",
            "Stop 2",
            "Stop 3"
        ],
        "createdBy": "test_user_id",
        "active": True
    }
    mock_route_doc = MagicMock()
    mock_route_doc.to_dict.return_value = route
    mock_route_doc.id = "1"

    # mock query behavior
    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_route_doc]
    mock_routes_collection.return_value = mock_query

    # mock db and batch
    mock_batch = MagicMock()
    mock_db = MagicMock()
    mock_db.batch.return_value = mock_batch
    mock_get_db.return_value = mock_db

    expected = (
        json.dumps({
            "message": "OK",
            "data": {
                "deletedRouteCount": 1,
                "deletedRouteIds": ["1"]
            }
        }),
        200,
        {
            "Content-Type": "application/json"
        }
    )
    
    response = delete_routes()

    assert response == expected

# create_route tests
@patch("main.get_routes_collection")
def test_create_route_success(mock_routes_collection):
    route = {
        "name": "Sample Route",
        "stops": [
            "Stop 1",
            "Stop 2",
            "Stop 3"
        ],
        "active": True
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

    # mock routes collection
    mock_routes = MagicMock()
    mock_routes_collection.return_value = mock_routes

    # mock request data
    data = route

    response = create_route(data)

    assert response == expected

@pytest.mark.parametrize("invalid_data", [
    {
        "name": "",
        "stops": [
            "Stop 1",
            "Stop 2",
            "Stop 3"
        ],
        "active": True
    },
    {
        "name": "sample_route",
        "stops": [
            "Stop 1",
            "Stop 2",
            "Stop 3"
        ],
        "active": True
    },
    {
        "name": None,
        "stops": [
            "Stop 1",
            "Stop 2",
            "Stop 3"
        ],
        "active": True
    },
    {
        "stops": [
            "Stop 1",
            "Stop 2",
            "Stop 3"
        ],
        "active": True
    }
])
@patch("main.get_routes_collection")
def test_create_route_invalid_name_fail(mock_routes_collection, invalid_data):
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

    # mock routes collection
    mock_routes = MagicMock()
    mock_routes_collection.return_value = mock_routes

    response = create_route(invalid_data)

    assert response == expected

@pytest.mark.parametrize("invalid_data", [
    {
        "name": "Sample Route",
        "stops": [
            1,
            2,
            3
        ],
        "active": True
    },
    {
        "name": "Sample Route",
        "stops": "",
        "active": True
    },
    {
        "name": "Sample Route",
        "active": True
    },
    {
        "name": "Sample Route",
        "stops": None,
        "active": True
    }
])
@patch("main.get_routes_collection")
def test_create_route_invalid_stops_fail(mock_routes_collection, invalid_data):
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

    # mock routes collection
    mock_routes = MagicMock()
    mock_routes_collection.return_value = mock_routes

    response = create_route(invalid_data)

    assert response == expected

@pytest.mark.parametrize("invalid_data", [
    {
        "name": "Sample Route",
        "stops": [
            "Stop 1",
            "Stop 2",
            "Stop 3"
        ],
        "active": ""
    },
    {
        "name": "Sample Route",
        "stops": [
            "Stop 1",
            "Stop 2",
            "Stop 3"
        ],
        "active": None
    },
    {
        "name": "Sample Route",
        "stops": [
            "Stop 1",
            "Stop 2",
            "Stop 3"
        ]
    }
])
@patch("main.get_routes_collection")
def test_create_route_invalid_active_status_fail(mock_routes_collection, invalid_data):
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

    # mock routes collection
    mock_routes = MagicMock()
    mock_routes_collection.return_value = mock_routes

    response = create_route(invalid_data)

    assert response == expected
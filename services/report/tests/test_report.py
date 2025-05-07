import pytest
from unittest.mock import MagicMock, patch
from main import get_reports, delete_reports, create_report, get_report
import json

# get_reports tests
@patch("main.get_reports_collection")
def test_get_reports_success(mock_reports_collection):
    report = {
        "id": "1",
        "type": "delay",
        "route": "Sample Route",
        "stop": "Stop 2",
        "timestamp": "test_timestamp",
        "createdBy": "test_user_id"
    }

    mock_report_doc = MagicMock()
    mock_report_doc.to_dict.return_value = report

    expected = (
        json.dumps({
            "message": "OK",
            "data": {
                "reports": [report]
            }
        }),
        200,
        {
            "Content-Type": "application/json"
        }
    )

    # mock query behavior
    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_report_doc]
    mock_reports_collection.return_value = mock_query
    
    response = get_reports()

    assert response == expected

# delete_routes tests
@patch("main.get_db")
@patch("main.get_reports_collection")
def test_delete_reports_success(mock_reports_collection, mock_get_db):
    report = {
        "id": "1",
        "type": "delay",
        "route": "Sample Route",
        "stop": "Stop 2",
        "timestamp": "test_timestamp",
        "createdBy": "test_user_id"
    }

    mock_report_doc = MagicMock()
    mock_report_doc.to_dict.return_value = report
    mock_report_doc.id = "1"

    # mock query behavior
    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_report_doc]
    mock_reports_collection.return_value = mock_query

    # mock db and batch
    mock_batch = MagicMock()
    mock_db = MagicMock()
    mock_db.batch.return_value = mock_batch
    mock_get_db.return_value = mock_db

    expected = (
        json.dumps({
            "message": "OK",
            "data": {
                "deletedReportCount": 1,
                "deletedReportIds": ["1"]
            }
        }),
        200,
        {
            "Content-Type": "application/json"
        }
    )
    
    response = delete_reports()

    assert response == expected

# create_report tests
@patch("main.get_reports_collection")
def test_create_report_success(mock_reports_collection):
    report = {
        "id": "1",
        "type": "delay",
        "route": "Sample Route",
        "stop": "Stop 2",
        "timestamp": "test_timestamp",
        "createdBy": "test_user_id"
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

    # mock reports collection
    mock_reports = MagicMock()
    mock_reports_collection.return_value = mock_reports

    # mock request data
    data = report

    response = create_report(data)

    assert response == expected

@pytest.mark.parametrize("invalid_data", [0, None, "", "some_type"])
@patch("main.get_reports_collection")
def test_create_report_invalid_type_fail(mock_reports_collection, invalid_data):
    report = {
        "id": "1",
        "type": invalid_data,
        "route": "Sample Route",
        "stop": "Stop 2",
        "timestamp": "test_timestamp",
        "createdBy": "test_user_id"
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

    # mock reports collection
    mock_reports = MagicMock()
    mock_reports_collection.return_value = mock_reports

    response = create_report(report)

    assert response == expected

@pytest.mark.parametrize("invalid_data", [0, None, "", "some_route"])
@patch("main.get_reports_collection")
def test_create_report_invalid_route_fail(mock_reports_collection, invalid_data):
    report = {
        "id": "1",
        "type": "delay",
        "route": invalid_data,
        "stop": "Stop 2",
        "timestamp": "test_timestamp",
        "createdBy": "test_user_id"
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

    # mock reports collection
    mock_reports = MagicMock()
    mock_reports_collection.return_value = mock_reports

    response = create_report(report)

    assert response == expected

# get_report tests
@patch("main.get_reports_collection")
def test_get_report_success(mock_reports_collection):
    report = {
        "id": "1",
        "type": "delay",
        "route": "Sample Route",
        "stop": "Stop 2",
        "timestamp": "test_timestamp",
        "createdBy": "test_user_id"
    }

    mock_report_doc = MagicMock()
    mock_report_doc.to_dict.return_value = report

    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_report_doc]

    mock_collection = MagicMock()
    mock_collection.where.return_value = mock_query

    mock_reports_collection.return_value = mock_collection

    expected = (
        json.dumps({
            "message": "OK",
            "data": {
                "report": report
            }
        }),
        200,
        {
            "Content-Type": "application/json"
        }
    )
    
    response = get_report(report["id"])

    assert response == expected

@patch("main.get_reports_collection")
@pytest.mark.parametrize("invalid_data", ["", 0, None])
def test_get_report_invalid_id_fail(mock_reports_collection, invalid_data):
    mock_collection = MagicMock()
    mock_reports_collection.return_value = mock_collection

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

    response = get_report(invalid_data)

    assert response == expected
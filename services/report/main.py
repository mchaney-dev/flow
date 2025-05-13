### DEVELOPMENT ###
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from common import logging
from common import configure_logging, get_db, get_collection, http_response, process_params
from common import is_valid_email, is_valid_password
### DEVELOPMENT ###

STATUS = {
    200: "OK",
    201: "Created",
    400: "Bad Request",
    401: "Unauthorized",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    500: "Internal Server Error"
}

def get_db():
    return firestore.Client()

def get_reports_collection():
    db = get_db()
    return db.collection("reports")

def request_handler(request):
    try:
        # default to using an empty dict if data is None
        data = request.get_json(silent=True) or {}
        logging.debug(f"Raw request data: {data}")

        # split parts of the path up into a list
        path = request.path.strip("/").split("/")
        # store query parameters
        query_params = request.args
        logging.debug(f"Query parameters: {query_params}")

        # dynamically parse path parameters
        report_id = ""
        if len(path) == 2 and path[0] == "reports":
            report_id = path[1]
            logging.debug(f"Report ID path parameter: {report_id}")

        # route HTTP requests based on endpoint
        match path:
            # endpoint for managing all reports
            case ["reports"]:
                match request.method:
                    # get a list of all reports
                    case "GET":
                        return get_reports(query_params)
                    # delete all reports
                    case "DELETE":
                        return delete_reports(query_params)
                    case "POST":
                        return create_report(data)
                    # handle invalid request method
                    case _:
                        logging.error(f"Invalid request method: {request.method}")
                        return http_response(405)
                    
            # /reports/{id}, endpoint for managing a specific report
            case ["reports", report_id]:
                match request.method:
                    # get a report
                    case "GET":
                        return get_report(report_id)
                    # handle invalid request method
                    case _:
                        logging.error(f"Invalid request method: {request.method}")
                        return http_response(405)
            # handle invalid endpoint
            case _:
                logging.error(f"Invalid resource: {request.path}")
                return http_response(404)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# utility function to form a consistent HTTP response
def http_response(status: int, data=None):
    try:
        if data is None:
            data = ""
        
        response_data = {
            "message": STATUS.get(status, "Unknown status"),
            "data": data
        }
        # google cloud expects a tuple
        response = (
            json.dumps(response_data),
            status, 
            {"Content-Type": "application/json"}
        )
        logging.debug(f"Raw response data: {response}")
        return response
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return (
            json.dumps({"message": STATUS[500], "data": ""}),
            500,
            {"Content-Type": "application/json"}
        )

# GET /reports
def get_reports(query_params=None):
    reports = get_reports_collection()
    query = reports
    docs = []

    # query params not implemented yet
    if query_params:
        return NotImplementedError()
    
    try:
        docs = list(query.stream())
        query_result = [doc.to_dict() for doc in docs]

        data = {
            "reports": query_result
        }

        return http_response(200, data)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# DELETE /reports
def delete_reports(query_params=None):
    try:
        db = get_db()
        reports = get_reports_collection()
        query = reports

        # query params not implemented yet
        if query_params:
            return NotImplementedError()
        
        docs = list(query.stream())

        batch = db.batch()
        deleted_ids = []

        for i, doc in enumerate(docs):
            batch.delete(doc.reference)
            deleted_ids.append(doc.id)

            # commit every 500 deletes for batch deleting
            if (i + 1) % 500 == 0:
                batch.commit()
                batch = db.batch()
        # commit remaining deletes
        if len(docs) % 500 != 0:
            batch.commit()
        
        data = {
            "deletedReportCount": len(deleted_ids),
            "deletedReportIds": deleted_ids
        }

        return http_response(200, data)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# POST /reports
def create_report(data):
    try:
        reports = get_reports_collection()
        query = reports
        report_types = [
            "delay",
            "no-show",
            "early departure",
            "route change",
            "overcrowding",
            "missed stop",
            "accessibility issues"
        ]

        # account for missing fields
        if not data.get("type"):
            logging.error(f"Missing 'type' in request body")
            return http_response(400)
        if not data.get("route"):
            logging.error(f"Missing 'route' in request body")
            return http_response(400)
        if not data.get("timestamp"):
            # TODO: automatically generate timestamp
            logging.error(f"Missing 'timestamp' in request body")
            return http_response(400)
        if not data.get("createdBy"):
            # TODO: automatically generate createdBy
            logging.error(f"Missing 'createdBy' in request body")
            return http_response(400)

        # invalid report type
        if data["type"] not in report_types:
            logging.error(f"Invalid report type: {data['type']}")
            return http_response(400)
        
        # normalize report type
        report_type = data["type"].strip()
        report_type = re.sub(r"\s+", " ", report_type)
        report_type = report_type.title()

        # normalize route name
        route = data["route"].strip()
        route = re.sub(r"\s+", " ", route)
        route = route.title()

        # normalize stop name
        if data.get("stop"):
            if not isinstance(data["stop"], str) or data["stop"] == "":
                logging.error(f"Invalid stop type: {type(data['stop'])}, must be string")
                return http_response(400)
            stop = data["stop"].strip()
            stop = re.sub(r"\s+", " ", stop)
            stop = stop.title()
            # invalid stop
            if re.match(r"^[A-Za-z0-9\s-]+$", stop) is None:
                logging.error(f"Invalid stop name: {stop}. Cannot contain special characters or underscores.")
                return http_response(400)

        # invalid route
        if re.match(r"^[A-Za-z0-9\s-]+$", route) is None:
            logging.error(f"Invalid route name: {route}. Cannot contain special characters or underscores.")
            return http_response(400)
        
        # create new report
        doc = reports.document()
        report_id = doc.id
        # id is automatically generated
        data["id"] = report_id
        data["route"] = route
        if data.get("stop"):
            data["stop"] = stop
        data["timestamp"] = "test_timestamp"
        # TODO: generate createdBy with authentication
        data["createdBy"] = "test_user_id"
        doc.set(data)

        return http_response(201)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# GET /reports/{id}
def get_report(report_id):
    reports = get_reports_collection()
    query = reports
    docs = []
    
    try:
        if not isinstance(report_id, str) or report_id == "":
            logging.error(f"Invalid report ID: {report_id}, must be string")
            return http_response(404)
        else:
            docs = list(query.where("id", "==", report_id).stream())
            if not docs:
                logging.error(f"Report with ID {report_id} not found")
                return http_response(404)
            # check if more than one report with the same ID exists
            if len(docs) > 1:
                logging.error(f"Multiple reports with ID {report_id} found")
                return http_response(500)
        
            data = {
                "report": docs[0].to_dict()
            }

            return http_response(200, data)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)
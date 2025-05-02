from google.cloud import firestore
import json
import logging

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
                    # update a report
                    case "PATCH":
                        return update_report(report_id, data)
                    # delete a report
                    case "DELETE":
                        return delete_report(report_id)
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
    pass

# DELETE /reports
def delete_reports(query_params=None):
    pass

# POST /reports
def create_report(data):
    pass

# GET /reports/{id}
def get_report(report_id):
    pass

# PATCH /reports/{id}
def update_report(report_id, data):
    pass

# DELETE /report/{id}
def delete_report(report_id):
    pass
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

def get_routes_collection():
    db = get_db()
    return db.collection("routes")

def request_handler(request):
    try:
        pass
    except Exception as e:
        pass

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
    
# GET /routes
def get_routes(query_params=None):
    pass

# POST /routes
def create_route(data):
    pass

# DELETE /routes
def delete_routes(query_params=None):
    pass

# GET /routes/{id}
def get_route():
    pass

# PATCH /routes/{id}
def update_route(data):
    pass

# DELETE /routes/{id}
def delete_route():
    pass
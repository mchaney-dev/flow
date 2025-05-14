from google.cloud import firestore
import json
import logging
import re

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

ENABLE_LOGGING = True

def configure_logging():
    # configure logging for all services
    # disable all logs if ENABLE_LOGGING is false
    if not ENABLE_LOGGING:
        logging.disable()
    else:
        # log format is "[LEVEL] [MM/DD/YY HH:MM:SS] - MESSAGE"
        logging.basicConfig(
            level=logging.DEBUG,
            format='[%(levelname)s] [%(asctime)s] - %(message)s',
            datefmt='%m/%d/%y %H:%M:%S'
    )

"""
A utility function to call a Firestore database instance, useful for unit tests or batch operations.
"""
def get_db():
    return firestore.Client()

"""
A utility function to get a named collection from a Firestore database.
collection_name (string): the name of the collection
"""
def get_collection(collection_name: str):
    db = get_db()
    return db.collection(collection_name)

"""
A utility function to form a consistent HTTP response.
status (int): the HTTP status code to return
data: the data to return, defaults to None
"""
def http_response(status: int, data=None):
    try:
        if data is None:
            data = ""

        if status > 201:
            logging.error(f"{status}, {data}")
        
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

        return response
    except Exception as e:
        logging.error(f"500, {e}")
        return (
            json.dumps({"message": STATUS[500], "data": e}),
            500,
            {"Content-Type": "application/json"}
        )

def process_params(request_data) -> tuple:
    # split parts of the path up into a list
    path = request_data.path.strip("/").split("/")
    # store query parameters
    query_params = request_data.args
    logging.debug(f"Query parameters: {query_params}")

    # dynamically parse path parameters
    id_param = None
    for part in path:
        part_segments = part.strip("/").split("/")
        for i, segment in enumerate(part_segments):
            # check for an id parameter
            if segment == "id" and i < len(path):
                id_param = path[i]
                break
    logging.debug(f"ID path parameter: {id_param}")
    
    return (path, id_param, query_params)

def is_valid_email(email: str):
    try:
        if email == "" or email == None:
            return False
        # normalize email
        email = email.strip().lower()
        # invalid email
        if re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is None:
            return False
        return email
    except Exception as e:
        raise e

def is_valid_password(password: str):
    try:
        if password == "" or password == None:
            return False
        if re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{8,}$", password) is None:
            return False
        return password
    except Exception as e:
        raise e
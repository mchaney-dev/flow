from google.cloud import firestore
import json
import logging
import base64
import bcrypt
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

def get_db():
    return firestore.Client()

def get_users_collection():
    db = get_db()
    return db.collection("users")

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
        user_id = ""
        if len(path) == 2 and path[0] == "users":
            if path[1] not in ["register", "login"]:
                user_id = path[1]
                logging.debug(f"User ID path parameter: {user_id}")

        # route HTTP requests based on endpoint
        match path:
            # /users, admin endpoint for managing all users
            case ["users"]:
                match request.method:
                    # get a list of all user accounts
                    case "GET":
                        return get_users(query_params)
                    # delete all user accounts
                    case "DELETE":
                        return delete_users(query_params)
                    # handle invalid request method
                    case _:
                        logging.error(f"Invalid request method: {request.method}")
                        return http_response(405)
            
            # /users/register, endpoint for registering a new user account
            case ["users", "register"]:
                match request.method:
                    # register a new user account
                    case "POST":
                        return register_user(data)
                    # handle invalid request method
                    case _:
                        logging.error(f"Invalid request method: {request.method}")
                        return http_response(405)
            
            # /users/login, endpoint for logging in with an existing user account
            case ["users", "login"]:
                match request.method:
                    # login a user account
                    case "POST":
                        return login_user(data)
                    # handle invalid request method
                    case _:
                        logging.error(f"Invalid request method: {request.method}")
                        return http_response(405)
                    
            # /users/{id}, endpoint for managing a specific user account
            case ["users", user_id]:
                match request.method:
                    # get a user account
                    case "GET":
                        return get_user(user_id)
                    # update a user account
                    case "PATCH":
                        return update_user(user_id)
                    # delete a user account
                    case "DELETE":
                        return delete_user(user_id)
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

# GET /users
def get_users(query_params=None):
    users = get_users_collection()
    query = users
    limit = None
    docs = []
    next_page_token = ""

    if query_params:
        # filter - AccountType
        if "type" in query_params:
            # account for invalid type
            if "type" in ["user", "admin"]:
                query = query.where("type", "==", query_params["type"])
            else:
                logging.error(f"Invalid type: {query_params['type']}")
                return http_response(400)
        
        # filter - pagination limit
        if "limit" in query_params:
            # account for invalid limit
            if limit is int and limit > 0:
                limit = int(query_params["limit"])
                query = query.limit(limit)
            else:
                logging.error(f"Invalid limit: {query_params['limit']}")
                return http_response(400)

        # filter - pagination start_after
        if "start_after" in query_params:
            try:
                doc_id = query_params["start_after"]
                # decode base64 nextPageToken
                doc_id = base64.urlsafe_b64decode(doc_id.encode()).decode()
                logging.debug(f"Decoded next page token: {doc_id}")

                last_doc = users.document(doc_id).get()
                if last_doc.exists:
                    query = query.start_after(last_doc)
                else:
                    logging.error(f"Invalid start_after ID: {query_params['start_after']}")
                    return http_response(400)
            except Exception as e:
                logging.error(f"Internal server error: {e}")
                return http_response(500)
    
    try:
        docs = list(query.stream())
        query_result = [doc.to_dict() for doc in docs]

        # add base64-encoded pagination token if needed
        if limit and len(docs) == limit:
            last_doc_id = docs[-1].id
            next_page_token = base64.urlsafe_b64encode(last_doc_id.encode()).decode()

        data = {
            "users": query_result,
            "nextPageToken": next_page_token
        }

        return http_response(200, data)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# DELETE /users
def delete_users(query_params=None):
    try:
        db = get_db()
        users = get_users_collection()
        query = users

        if query_params:
            # filter - AccountType
            if "type" in query_params:
                # account for invalid type
                if query_params["type"] in ["user", "admin"]:
                    query = query.where("type", "==", query_params["type"])
                else:
                    logging.error(f"Invalid type: {query_params['type']}")
                    return http_response(400)
        
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
            "deletedUserCount": len(deleted_ids),
            "deletedUserIds": deleted_ids
        }

        return http_response(200, data)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# POST /users/register
def register_user(data):
    try:
        users = get_users_collection()
        query = users

        # account for missing fields
        if not data.get("email"):
            logging.error(f"Missing 'email' in request body")
            return http_response(400)
        if not data.get("password"):
            logging.error(f"Missing 'password' in request body")
            return http_response(400)
        if not data.get("type"):
            logging.error(f"Missing 'type' in request body")
            return http_response(400)
        
        email = data["email"].strip().lower()

        # account for invalid fields
        # invalid email
        if re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is None:
            logging.error(f"Invalid email: {email}")
            return http_response(400)
        # invalid password
        if re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{8,}$", data.get("password")) is None:
            logging.error(f"Invalid password. Must be at least 8 characters, contain at least one uppercase and one lowercase letter, at least one digit, and at least one special character: !, @, #, $, %, ^, &, *, (, )")
            return http_response(400)
        # invalid type
        if data.get("type") not in ["user", "admin"]:
            logging.error(f"Invalid user type: {data.get('type')}")
            return http_response(400)
    
        password = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # check for accounts that already use this email
        registered_email = query.where("email", "==", email).limit(1).stream()
        if any(registered_email):
            logging.error(f"Email already in use")
            return http_response(409)

        # create new user
        doc = users.document()
        user_id = doc.id
        # id is automatically generated
        data["id"] = user_id
        data["email"] = email
        data["password"] = password
        doc.set(data)

        return http_response(201)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# POST /users/login
def login_user(data):
    try:
        users = get_users_collection()
        query = users

        if not data.get("email"):
            logging.error(f"Missing 'email' in request body")
            http_response(400)
        if not data.get("password"):
            logging.error(f"Missing 'password' in request body")
            http_response(400)

        email = data["email"].strip().lower()
        password = data["password"]

        query_result = query.where("email", "==", email).limit(1).stream()
        doc = next(iter(query_result), None)
        
        user_data = doc.to_dict()
        stored_password = user_data.get("password", "")
        # verify password
        if not bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
            logging.error(f"Invalid password")
            return http_response(401)
        
        return http_response(200)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# GET /users/{id}
def get_user():
    pass

# PATCH /users/{id}
def update_user(data):
    pass

# DELETE /users/{id}
def delete_user():
    pass
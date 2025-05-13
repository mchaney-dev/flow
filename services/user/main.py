import base64
import bcrypt

### DEVELOPMENT ###
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from common import logging
from common import configure_logging, get_db, get_collection, http_response, process_params
from common import is_valid_email, is_valid_password
### DEVELOPMENT ###

user_types = [
    "user",
    "admin"
]

def request_handler(request):
    try:
        configure_logging()

        # default to using an empty dict if data is None
        data = request.get_json(silent=True) or {}
        logging.debug(f"Raw request data: {data}")

        # dynamically process parameters
        path, id_param, query_params = process_params(data)

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
                        return http_response(
                            405, 
                            f"Invalid request method: {request.method}, " +
                            f"allowed methods are 'GET', 'DELETE'"
                        )
            
            # /users/register, endpoint for registering a new user account
            case ["users", "register"]:
                match request.method:
                    # register a new user account
                    case "POST":
                        return register_user(data)
                    # handle invalid request method
                    case _:
                        return http_response(
                            405, 
                            f"Invalid request method: {request.method}, " +
                            f"allowed method is 'POST'"
                        )
            
            # /users/login, endpoint for logging in with an existing user account
            case ["users", "login"]:
                match request.method:
                    # login a user account
                    case "POST":
                        return login_user(data)
                    # handle invalid request method
                    case _:
                        return http_response(
                            405,
                            f"Invalid request method: {request.method}, " +
                            f"allowed method is 'POST'"
                        )
                    
            # /users/{id}, endpoint for managing a specific user account
            case ["users", id_param]:
                match request.method:
                    # get a user account
                    case "GET":
                        return get_user(id_param)
                    # update a user account
                    case "PATCH":
                        return update_user(id_param, data)
                    # delete a user account
                    case "DELETE":
                        return delete_user(id_param)
                    # handle invalid request method
                    case _:
                        return http_response(
                            405,
                            f"Invalid request method: {request.method}, " +
                            f"allowed methods are 'GET', 'PATCH', 'DELETE'"
                        )
            
            # /users/{id}/password, endpoint for password management
            case ["users", id_param, "password"]:
                match request.method:
                    # update a user's password
                    case "PATCH":
                        return update_password(id_param, data)
                    # handle invalid request method
                    case _:
                        return http_response(
                            405,
                            f"Invalid request method: {request.method}, " +
                            f"allowed method is 'PATCH'"
                        )
            
            # handle invalid path
            case _:
                return http_response(
                    404,
                    f"Invalid resource: {request.path}"
                )
    
    except Exception as e:
        return http_response(
            500,
            f"{e}"
        )

# GET /users
def get_users(query_params: dict = None):
    try:
        users = get_collection("users")
        query = users
        docs = []
        next_page_token = ""

        # process any query parameters
        if query_params:
            # filter - account type
            if query_params.get("type"):
                # account for invalid type
                if not isinstance(query_params["type"], str) or query_params["type"] not in user_types:
                    return http_response(
                        400, 
                        f"Invalid query parameter 'type': {query_params['type']} ({type(query_params['type'])}), " +
                        f"must be of type 'string' and one of the following: {user_types}"
                    )
                else:
                    query = query.where("type", "==", query_params["type"])

            # filter - pagination limit
            if query_params.get("limit"):
                # account for invalid limit
                if isinstance(query_params["limit"], str) and int(query_params["limit"]) > 0:
                    query = query.limit(int(query_params["limit"]))
                else:
                    return http_response(
                        400, 
                        f"Invalid query parameter 'limit': {query_params['limit']} ({type(query_params['limit'])}), " +
                        f"must be of type 'string' and between 1-50"
                    )
            
            # filter - pagination start_after
            if query_params.get("start_after"):
                # account for invalid start_after ID
                if isinstance(query_params["start_after"], str) and int(query_params["start_after"]) >= 0:
                    doc_id = query_params["start_after"]
                    # set the query start_after id
                    doc_id = base64.urlsafe_b64decode(doc_id.encode()).decode()
                    last_doc = users.document(doc_id).get()
                    if last_doc.exists:
                        query = query.start_after(last_doc)
                    else:
                        return http_response(
                            400,
                            f"Invalid start_after ID: {query_params['start_after']}, " +
                            f"document does not exist"
                        )
                else:
                    return http_response(
                        400,
                        f"Invalid start_after ID: {query_params['start_after']} ({type(query_params['start_after'])}), " +
                        f"must be of type 'string' and greater than or equal to 0"
                    )

        # query the database
        docs = list(query.stream())
        query_result = [doc.to_dict() for doc in docs]

        # add base64-encoded pagination token if needed
        if query_params and query_params.get("limit") and len(docs) == int(query_params["limit"]):
            last_doc_id = docs[-1].id
            next_page_token = base64.urlsafe_b64encode(last_doc_id.encode()).decode()

        # form response
        data = {
            "users": query_result,
            "nextPageToken": next_page_token
        }

        return http_response(200, data)
    except Exception as e:
        return http_response(
            500, 
            f"{e}"
        )

# DELETE /users
def delete_users(query_params: dict = None):
    try:
        db = get_db()
        users = get_collection("users")
        query = users

        if query_params:
            # filter - account type
            if query_params.get("type"):
                if isinstance(query_params["type"], str) and "type" in user_types:
                    query = query.where("type", "==", query_params["type"])
                else:
                    return http_response(
                        400, 
                        f"Invalid query parameter 'type': {query_params['type']} ({type(query_params['type'])}), " +
                        f"must be of type 'string' and one of the following: {user_types}"
                    )
        
        # query the database
        docs = list(query.stream())

        # delete accounts in batches
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
        
        # form response
        data = {
            "deletedUserCount": len(deleted_ids),
            "deletedUserIds": deleted_ids
        }

        return http_response(200, data)
    except Exception as e:
        return http_response(
            500, 
            f"{e}"
        )

# POST /users/register
def register_user(data: dict):
    try:
        users = get_collection("users")
        query = users

        # account for missing fields
        if not data.get("email"):
            return http_response(
                400,
                f"Missing required field 'email' in request body"
            )
        if not data.get("password"):
            return http_response(
                400,
                f"Missing required field 'password' in request body"
            )
        if not data.get("type"):
            return http_response(
                400,
                f"Missing required field 'type' in request body"
            )

        # account for invalid fields
        # invalid email
        if not is_valid_email(data["email"]):
            return http_response(
                400,
                f"Invalid field 'email': {data['email']}"
            )
        else:
            email = is_valid_email(data["email"])
        # check for accounts that already use this email
        registered_email = query.where("email", "==", email).limit(1).stream()
        if any(registered_email):
            return http_response(
                409,
                f"Invalid field 'email': {email}, " +
                f"email already in use"
            )
        
        # invalid password
        if not is_valid_password(data["password"]):
            return http_response(
                400,
                f"Invalid field 'password': {data['password']}"
            )
        else:
            password = is_valid_password(data["password"])
        # hash password
        password = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        
        # invalid type
        if not isinstance(data["type"], str) or data["type"] not in user_types:
            return http_response(
                400,
                f"Invalid user type: {data.get('type')} ({type(data['type'])}), " +
                f"must be of type 'string' and one of the following: {user_types}"
            )

        # create new user
        doc = users.document()
        data["id"] = doc.id
        data["email"] = email
        data["password"] = password
        doc.set(data)

        return http_response(201)
    except Exception as e:
        return http_response(
            500,
            f"{e}"
        )

# POST /users/login
def login_user(data: dict):
    try:
        users = get_collection("users")
        query = users

        # account for missing fields
        if not data.get("email"):
            http_response(
                400,
                f"Missing required field 'email' in request body"
            )
        if not data.get("password"):
            http_response(
                400,
                f"Missing required field 'password' in request body"
            )

        # account for invalid fields
        # invalid email
        if not is_valid_email(data["email"]):
            return http_response(
                400,
                f"Invalid field 'email': {data['email']}"
            )
        else:
            email = is_valid_email(data["email"])
        
        # invalid password
        if not is_valid_password(data["password"]):
            return http_response(
                400,
                f"Invalid field 'password': {data['password']}"
            )
        else:
            password = is_valid_password(data["password"])

        # get user account matching email
        query_result = query.where("email", "==", email).limit(1).stream()
        doc = next(iter(query_result), None)
        if not doc:
            return http_response(
                404,
                f"Invalid field 'email': {email}, " +
                f"associated user account does not exist"
            )
        user_data = doc.to_dict()

        # verify password
        stored_password = user_data.get("password", "")
        if not bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
            return http_response(
                401,
                f"Invalid field 'password': {password}, " +
                f"password is incorrect"
            )
        
        return http_response(200)
    except Exception as e:
        return http_response(
            500,
            f"{e}"
        )

# GET /users/{id}
def get_user(user_id: str):
    try:
        users = get_collection("users")
        query = users

        # account for missing fields
        # invalid id
        if user_id == "":
            return http_response(
                400,
                f"Required field 'user_id' must not be empty string"
            )
        
        # query database
        query_result = query.where("id", "==", user_id).limit(1).stream()
        doc = next(iter(query_result), None)
        if not doc:
            return http_response(
                400,
                f"Invalid field 'user_id': {user_id}, " +
                f"associated user account does not exist"
            )
        
        # form response
        data = {
            "user": doc.to_dict(),
        }

        return http_response(200, data)
    except Exception as e:
        return http_response(
            500,
            f"{e}"
        )

# PATCH /users/{id}
def update_user(user_id: str, data: dict):
    try:
        users = get_collection("users")
        db = get_db()
        query = users

        updates = {}

        # account for invalid user_id
        if user_id == "":
            return http_response(
                400,
                f"Required field 'user_id' must not be empty string"
            )
        
        if "email" in data.keys():
            # account for invalid email
            if not is_valid_email(data["email"]):
                return http_response(
                    400,
                    f"Invalid field 'email': {data['email']}"
                )
            else:
                email = is_valid_email(data["email"])
            # check for accounts that already use this email
            registered_email = query.where("email", "==", email).limit(1).stream()
            if any(registered_email):
                return http_response(
                    409,
                    f"Invalid field 'email': {email}, " +
                    f"email already in use"
                )
            updates.update({"email": email})
        
        if "type" in data.keys():
            # account for invalid type
            if not isinstance(data["type"], str) or data["type"] not in user_types:
                return http_response(
                    400,
                    f"Invalid user type: {data.get('type')} ({type(data['type'])}), " +
                    f"must be of type 'string' and one of the following: {user_types}"
                )
        updates.update({"type": data["type"]})

        # query database
        query_result = query.where("id", "==", user_id).limit(1).stream()
        doc = next(iter(query_result), None)
        if not doc:
            return http_response(
                404,
                f"User with ID {user_id} not found"
            )

        # update user
        user_ref = db.collection("users").document(doc.id)
        user_ref.update(updates)

        return http_response(200)
    except Exception as e:
        return http_response(
            500,
            f"{e}"
        )

# DELETE /users/{id}
def delete_user(user_id: str):
    try:
        users = get_collection("users")
        query = users

        # account for invalid user_id
        if user_id == "":
            return http_response(
                400,
                f"Required field 'user_id' must not be empty string"
            )

        # query database
        query_result = query.where("id", "==", user_id).limit(1).stream()
        doc = next(iter(query_result), None)
        if not doc:
            return http_response(
                404,
                f"User with ID {user_id} not found"
            )

        # delete user
        doc.reference.delete()

        return http_response(200)
    except Exception as e:
        return http_response(
            500,
            f"{e}"
        )

# PATCH /users/{id}/password
def update_password(user_id: str, data: dict):
    try:
        users = get_collection("users")
        db = get_db()
        query = users

        # account for invalid user_id
        if user_id == "":
            return http_response(
                400,
                f"Required field 'user_id' must not be empty string"
            )

        # account for missing fields
        if not data.get("prevPassword"):
            http_response(
                400,
                f"Missing required field 'prevPassword' in request body"
            )
        if not data.get("newPassword"):
            http_response(
                400,
                f"Missing required field 'newPassword' in request body"
            )
        
        # account for invalid fields
        # invalid prevPassword
        if not is_valid_password(data["prevPassword"]):
            return http_response(
                400,
                f"Invalid field 'prevPassword': {data['prevPassword']}"
            )
        else:
            prev_password = is_valid_password(data["prevPassword"])
        
        # invalid newPassword
        if not is_valid_password(data["newPassword"]):
            return http_response(
                400,
                f"Invalid field 'newPassword': {data['newPassword']}"
            )
        else:
            new_password = is_valid_password(data["newPassword"])

        # passwords cannot match
        if prev_password == new_password:
            return http_response(
                400,
                "New password cannot match previous password"
            )

        # query database
        query_result = query.where("id", "==", user_id).limit(1).stream()
        doc = next(iter(query_result), None)
        if not doc:
            return http_response(
                404,
                f"User with ID {user_id} not found"
            )
        user_data = doc.to_dict()

        # verify stored password and prev_password are the same
        stored_password = user_data.get("password")
        if not stored_password or not bcrypt.checkpw(prev_password.encode("utf-8"), stored_password.encode("utf-8")):
            return http_response(
                401,
                "Previous password does not match stored password"
            )

        # hash new_password
        new_hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # update password
        user_ref = db.collection("users").document(doc.id)
        user_ref.update({"password": new_hashed_password})

        return http_response(200)
    except Exception as e:
        return http_response(
            500,
            f"{e}"
        )
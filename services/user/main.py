from google.cloud import firestore
import json

STATUS = {
    200: "OK",
    201: "Created",
    400: "Bad Request",
    401: "Unauthorized",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error"
}

# initialize firestore client
db = firestore.Client()
users = db.collection("users")

def request_handler(request):
    try:
        # default to using an empty dict if data is None
        data = request.get_json(silent=True) or {}

        # split parts of the path up into a list
        path = request.path.strip("/").split("/")
        # store query parameters
        query_params = request.args

        # dynamically parse path parameters
        if len(path) == 2 and path[0] == "users":
            if path[1] not in ["register", "login"]:
                user_id = path[1]

        # route HTTP requests based on endpoint
        match path:
            # /users, admin endpoint for managing all users
            case ["users"]:
                match request.method:
                    # get a list of all user accounts
                    case "GET":
                        return get_users()
                    # delete all user accounts
                    case "DELETE":
                        return delete_users()
                    # handle invalid request method
                    case _:
                        return http_response(405)
            
            # /users/register, endpoint for registering a new user account
            case ["users", "register"]:
                match request.method:
                    # register a new user account
                    case "POST":
                        return register_user(data)
                    # handle invalid request method
                    case _:
                        return http_response(405)
            
            # /users/login, endpoint for logging in with an existing user account
            case ["users", "login"]:
                match request.method:
                    # login a user account
                    case "POST":
                        return login_user(data)
                    # handle invalid request method
                    case _:
                        return http_response(404)
                    
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
                        return http_response(405)
            # handle invalid endpoint
            case _:
                return http_response(404, "Invalid endpoint.")
    except Exception as e:
        return http_response(500, f"Internal server error: {str(e)}")

# utility function to form a consistent HTTP response
def http_response(status: int):
    try:
        message = STATUS[status]
        # google cloud expects a tuple
        return (
            json.dumps({"message": message}), 
            status, 
            {"Content-Type": "application/json"}
        )
    except Exception as e:
        return (
            json.dumps({"message": STATUS[500]}),
            500,
            {"Content-Type": "application/json"}
        )

# GET /users
def get_users():
    pass

# DELETE /users
def delete_users():
    pass

# POST /users/register
def register_user():
    pass

# POST /users/login
def login_user():
    pass

# GET /users/{id}
def get_user():
    pass

# PATCH /users/{id}
def update_user():
    pass

# DELETE /users/{id}
def delete_user():
    pass
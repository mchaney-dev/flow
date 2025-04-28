from google.cloud import firestore
import json

# initialize firestore client
db = firestore.Client()
users = db.collection('users')

def request_handler(request):
    try:
        data = request.get_json()

        # route HTTP requests based on endpoint
        match request.path:
            # admin endpoint for managing all users
            case '/users':
                match request.method:
                    # get a list of all user accounts
                    case 'GET':
                        pass

                    # delete all user accounts
                    case 'DELETE':
                        pass

                    # handle invalid request method
                    case _:
                        return http_response(
                            404,
                            "Invalid request method.",
                            data
                        )
            
            # endpoint for registering a new user account
            case '/user/register':
                match request.method:
                    # register a new user account
                    case 'POST':
                        pass

                    # handle invalid request method
                    case _:
                        return http_response(
                            404,
                            "Invalid request method.",
                            data
                        )
            
            # endpoint for logging in with an existing user account
            case '/user/login':
                match request.method:
                    # login a user account
                    case 'POST':
                        pass

                    # handle invalid request method
                    case _:
                        return http_response(
                            404,
                            "Invalid request method.",
                            data
                        )
                    
            # endpoint for managing a specific user account
            case '/user':
                # TODO: check for user id in path parameters
                match request.method:
                    # get a user account
                    case 'GET':
                        pass

                    # update a user account
                    case 'PATCH':
                        pass

                    # delete a user account
                    case 'DELETE':
                        pass

                    # handle invalid request method
                    case _:
                        return http_response(
                            404,
                            "Invalid request method.",
                            data
                        )
            # handle invalid endpoint
            case _:
                return http_response(
                    400,
                    "Invalid endpoint.",
                    data
                )
    except Exception as e:
        return http_response(
            500,
            str(e),
            data
        )

# utility function to form a consistent HTTP response
def http_response(status: int, message: str, data: str):
    response = {
        "status": status,
        "headers": {
            "Content-Type": "application/json"
        },
        "message": message,
        "data": data
    }

    return json.dumps(response)
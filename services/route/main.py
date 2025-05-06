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

def get_db():
    return firestore.Client()

def get_routes_collection():
    db = get_db()
    return db.collection("routes")

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
        route_id = ""
        if len(path) == 2 and path[0] == "routes":
            route_id = path[1]
            logging.debug(f"Route ID path parameter: {route_id}")

       # route HTTP requests based on endpoint
        match path:
            # /routes, endpoint for managing all routes
            case ["routes"]:
                match request.method:
                    # get a list of all routes
                    case "GET":
                        return get_routes(query_params)
                    # delete all routes
                    case "DELETE":
                        return delete_routes(query_params)
                    # handle invalid request method
                    case _:
                        logging.error(f"Invalid request method: {request.method}")
                        return http_response(405)
            # /routes/{id}, endpoint for managing a specific route
            case ["routes", route_id]:
                match request.method:
                    # create a new route
                    case "POST":
                        return create_route(data)
                    # get a route
                    case "GET":
                        return get_route(route_id)
                    # update a route
                    case "PATCH":
                        return update_route(route_id, data)
                    # delete a route
                    case "DELETE":
                        return delete_route(route_id)
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
    
# GET /routes
def get_routes(query_params=None):
    routes = get_routes_collection()
    query = routes
    docs = []

    # query params not implemented yet
    if query_params:
        return NotImplementedError()
    
    try:
        docs = list(query.stream())
        query_result = [doc.to_dict() for doc in docs]

        data = {
            "routes": query_result
        }

        return http_response(200, data)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# DELETE /routes
def delete_routes(query_params=None):
    try:
        db = get_db()
        routes = get_routes_collection()
        query = routes

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
            "deletedRouteCount": len(deleted_ids),
            "deletedRouteIds": deleted_ids
        }

        return http_response(200, data)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# POST /routes
def create_route(data):
    try:
        routes = get_routes_collection()
        query = routes

        # account for missing fields
        if not data.get("name"):
            logging.error(f"Missing 'name' in request body")
            return http_response(400)
        if not data.get("stops"):
            logging.error(f"Missing 'stops' in request body")
            return http_response(400)
        if not data.get("active"):
            logging.error(f"Missing 'active' in request body")
            return http_response(400)
        
        # normalize route name
        name = data["name"].strip()
        name = re.sub(r"\s+", " ", name)
        name = name.title()

        # account for invalid fields
        # invalid name
        if re.match(r"^[A-Za-z0-9\s-]+$", name) is None:
            logging.error(f"Invalid route name: {name}. Cannot contain special characters or underscores.")
            return http_response(400)
        # invalid stops
        if isinstance(data["stops"], list):
            # normalize each stop in the list
            for stop in data["stops"]:
                if isinstance(stop, str):
                    stop = stop.strip()
                    stop = re.sub(r"\s+", " ", stop)
                    stop = stop.title()

                    if re.match(r"^[A-Za-z0-9\s-]+$", stop) is None:
                        logging.error(f"Invalid stop name: {stop}. Cannot contain special characters or underscores.")
                        return http_response(400)
                else:
                    logging.error(f"Stop must be a string")
                    return http_response(400)
        else:
            logging.error(f"Field 'stops' is of type {type(data['stops'])}, must be array of strings")
            return http_response(400)
        # invalid active status
        if not isinstance(data["active"], bool):
            logging.error(f"Invalid active status: {data['active']}. Must be a boolean")
            return http_response(400)
        
        # create new route
        doc = routes.document()
        route_id = doc.id
        # id is automatically generated
        data["id"] = route_id
        data["name"] = name
        # TODO: generate createdBy with authentication
        data["createdBy"] = "test_user_id"
        doc.set(data)

        return http_response(201)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# GET /routes/{id}
def get_route(route_id):
    routes = get_routes_collection()
    query = routes
    docs = []
    
    try:
        docs = list(query.where("id", "==", route_id).stream())
        if not docs:
            logging.error(f"Route with ID {route_id} not found")
            return http_response(404)
        # check if more than one route with the same ID exists
        if len(docs) > 1:
            logging.error(f"Multiple routes with ID {route_id} found")
            return http_response(500)
        
        data = {
            "route": docs[0].to_dict()
        }

        return http_response(200, data)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# PATCH /routes/{id}
def update_route(route_id, data):
    try:
        routes = get_routes_collection()
        db = get_db()
        query = routes

        updates = {}
        
        if not isinstance(route_id, str) or route_id == "":
            logging.error(f"Invalid route ID: {route_id}, must be string")
            return http_response(404)
        if "name" in data.keys():
            if not isinstance(data["name"], str):
                logging.error(f"Invalid route name: {data["name"]}, must be string")
                return http_response(400)
            # normalize route name
            name = data["name"].strip()
            name = re.sub(r"\s+", " ", name)
            name = name.title()

            # invalid name
            if re.match(r"^[A-Za-z0-9\s-]+$", name) is None:
                logging.error(f"Invalid route name: {name}. Cannot contain special characters or underscores.")
                return http_response(400)
            updates.update({"name": name})
        
        if "stops" in data.keys():
            # invalid stops
            if isinstance(data["stops"], list) and len(data["stops"]) > 0:
                # normalize each stop in the list
                normalized_stops = []
                for bus_stop in data["stops"]:
                    if isinstance(bus_stop, str) and bus_stop != "":
                        bus_stop = bus_stop.strip()
                        bus_stop = re.sub(r"\s+", " ", bus_stop)
                        bus_stop = bus_stop.title()

                        if re.match(r"^[A-Za-z0-9\s-]+$", bus_stop) is None:
                            logging.error(f"Invalid stop name: {bus_stop}. Cannot contain special characters or underscores.")
                            return http_response(400)
                    else:
                        logging.error(f"Stop must be a string")
                        return http_response(400)
                    normalized_stops.append(bus_stop)
            else:
                logging.error(f"Field 'stops' is of type {type(data['stops'])}, must be array of strings")
                return http_response(400)
            updates.update({"stops": normalized_stops})
            
        if "active" in data.keys():
            # invalid active status
            if not isinstance(data["active"], bool):
                logging.error(f"Invalid active status: {data['active']}. Must be a boolean")
                return http_response(400)
            updates.update({"active": data["active"]})
        
        docs = list(query.where("id", "==", route_id).stream())
        if not docs:
            logging.error(f"Route with ID {route_id} not found")
            return http_response(404)
        if len(docs) > 1:
            logging.error(f"Multiple routes with ID {route_id} found")
            return http_response(500)

        # update route
        route_ref = db.collection("routes").document(docs[0].id)
        route_ref.update(updates)

        return http_response(200)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# DELETE /routes/{id}
def delete_route(route_id):
    try:
        routes = get_routes_collection()
        query = routes
        docs = []

        if not isinstance(route_id, str) or route_id == "":
            logging.error(f"Invalid route ID: {route_id}, must be string")
            return http_response(404)
        docs = list(query.where("id", "==", route_id).stream())
        if not docs:
            logging.error(f"Route with ID {route_id} not found")
            return http_response(404)
        # check if more than one route with the same ID exists
        if len(docs) > 1:
            logging.error(f"Multiple routes with ID {route_id} found")
            return http_response(500)

        doc = docs[0]
        doc.reference.delete()

        return http_response(200)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)
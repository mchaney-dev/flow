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

def get_maps_collection():
    db = get_db()
    return db.collection("maps")

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
        map_id = ""
        if len(path) == 2 and path[0] == "maps":
            map_id = path[1]
            logging.debug(f"Map ID path parameter: {map_id}")

        # route HTTP requests based on endpoint
        match path:
            # endpoint for managing all maps
            case ["maps"]:
                match request.method:
                    # get a list of all maps
                    case "GET":
                        return get_maps(query_params)
                    # delete all maps
                    case "DELETE":
                        return delete_maps(query_params)
                    # upload a map
                    case "POST":
                        return create_map(data)
                    # handle invalid request method
                    case _:
                        logging.error(f"Invalid request method: {request.method}")
                        return http_response(405)
                    
            # /maps/{id}, endpoint for managing a specific map
            case ["maps", map_id]:
                match request.method:
                    # get a map
                    case "GET":
                        return get_map(map_id)
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

# GET /maps
def get_maps(query_params=None):
    maps = get_maps_collection()
    query = maps
    docs = []

    # query params not implemented yet
    if query_params:
        return NotImplementedError()
    
    try:
        docs = list(query.stream())
        query_result = [doc.to_dict() for doc in docs]

        data = {
            "maps": query_result
        }

        return http_response(200, data)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# DELETE /maps
def delete_maps(query_params=None):
    try:
        db = get_db()
        maps = get_maps_collection()
        query = maps

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
            "deletedMapCount": len(deleted_ids),
            "deletedMapIds": deleted_ids
        }

        return http_response(200, data)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# POST /maps
def create_map(data):
    try:
        maps = get_maps_collection()
        query = maps

        # account for missing fields
        if not data.get("url"):
            logging.error(f"Missing 'url' in request body")
            return http_response(400)

        if not isinstance(data["url"], str) or data["url"] == "":
            logging.error(f"Invalid url type: {type(data['url'])}, must be string")
            return http_response(400)
        
        # create new map
        doc = maps.document()
        map_id = doc.id
        # id is automatically generated
        data["id"] = map_id
        doc.set(data)

        return http_response(201)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)

# GET /maps/{id}
def get_map(map_id):
    maps = get_maps_collection()
    query = maps
    docs = []
    
    try:
        if not isinstance(map_id, str) or map_id == "":
            logging.error(f"Invalid map ID: {map_id}, must be string")
            return http_response(404)
        else:
            docs = list(query.where("id", "==", map_id).stream())
            if not docs:
                logging.error(f"Map with ID {map_id} not found")
                return http_response(404)
            # check if more than one report with the same ID exists
            if len(docs) > 1:
                logging.error(f"Multiple maps with ID {map_id} found")
                return http_response(500)
        
            data = {
                "map": docs[0].to_dict()
            }

            return http_response(200, data)
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return http_response(500)
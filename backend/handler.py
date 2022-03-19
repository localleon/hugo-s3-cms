import json
import io
import re
from subprocess import call
from warnings import catch_warnings
import boto3
import datetime

# Config Option -> migrate to env variables
bucket_name = "hugo-cms-store1"
s3 = boto3.client("s3")


def main_handler(event, context):
    print(event)

    req_path = event["rawPath"]

    # Routing inside the lambda function, we don't need multiple lambda functions for our api
    if req_path == "/upload":
        return handler_upload_post(event)
    elif req_path == "/list":
        return handler_list_directory()
    elif req_path == "/get":
        return handler_get_file(event)
    elif req_path == "/delete":
        return handler_delete_file(event)

    # TODO: Remove in production, only for testin

    return handler_catch_all()


def handler_catch_all(event):
    """This Handler shouldn't be called normally. AWS Gateway is handling 404 and invalid paths, but this can catch some edge cases"""
    return {
        "statusCode": 503,
        "body": {
            "error": "Error while trying to parse the path. Internal Server Error in Request Routing",
            "event": event,
        },
    }


def handler_get_file(event):
    """This handler returns the object for the given key"""
    print("Get File called. Not implemented")


def delete_file_from_s3(key):
    """Delete a file from key in our s3 object and form a correct http response"""

    # Check if the file really exists before deleting it
    if key not in list_objects_from_bucket():
        return (404, "Key was not found in bucket")

    # trigger the s3 file operation
    s3_resp = s3.delete_object(Bucket=bucket_name, Key=key)
    http_status_code = s3_resp["ResponseMetadata"]["HTTPStatusCode"]

    # at successfull operations we return normally, else we provide the user with the s3 statuscode and response metadata for debugging
    if http_status_code == 204:
        return (202, f"Successfully delete object with key {key}")
    else:
        return (http_status_code, s3_resp["ResponseMetadata"])


def handler_delete_file(event):
    """This handler deletes a specific object at the given key"""

    # Call the delete s3 function if we got a valid request
    body = get_body_from_event(event)

    if body != None:
        if "key" in body.keys():
            s3_resp = delete_file_from_s3(body["key"])
            return callback(s3_resp[0], s3_resp[1])

    return callback(
        401,
        {
            "msg": "Malformed Request. You didn't specify which object should be deleted with a key. Did you provide valid json?"
        },
    )


def handler_list_directory():
    """This handler returns the keys for all objects in the bucket"""
    objects = list_objects_from_bucket()
    return callback(202, {"Contents": objects})


def handler_upload_post(event):
    """Upload_post handles the uploading process of the api"""
    body = get_body_from_event(event)

    # Check if request is valid
    if not validate_upload_json(body):
        return callback(
            400, {"msg": "Malformed Request. Not all required json-keys where provided"}
        )

    # Create an in-memory file and write to aws s3
    post_file = create_post_file(params=body)
    write_to_s3(file=post_file, filename=get_filename_from_post(body["title"]))

    return callback(200, {"msg": "Post was created successfully"})


def list_objects_from_bucket():
    s3_resp = s3.list_objects_v2(Bucket=bucket_name, Delimiter="/")
    return [obj["Key"] for obj in s3_resp["Contents"]]


def get_body_from_event(event):
    return json.loads(event["body"]) if "body" in event.keys() else None


def get_filename_from_post(title):
    """Converts the titel to a filename (cut length at 20) and adds a timestamp"""
    short_title = title.replace(" ", "_")[:20]
    return f"{datetime.date.today().isoformat()}_{short_title}.md"


def write_to_s3(file, filename, path=None):
    print(f"Writing to {bucket_name} with {filename} in {path}")
    # construct the s3_key based on if the file should be stored in a folder
    s3_path = path + "/" + filename if path != None else filename

    return s3.upload_fileobj(file, bucket_name, s3_path)


def create_post_file(params):
    """Create_post_file builds a virtual file in memory and returns it"""
    metadata = f"---\ntitle: {params['title']}\ndate: {params['date']}\nauthor: {params['author']}\ndraft: false\n"
    content = f"---\n{params['content']}\n---\n"

    # we create a file in memory, content of markdown needs to be encoded into bytes
    md_file = io.BytesIO()
    md_file.write((metadata + content).encode("UTF-8"))
    md_file.seek(0)

    return md_file


def validate_upload_json(params):
    """Tkes the body of the requests and checks if every valid parameter for an upload is filled in"""
    required_keys = ("title", "date", "author", "content")
    return all(keys in params for keys in required_keys)


def callback(status_code, body):
    """Creates a API Gateway compatible response message."""
    return {"statusCode": status_code, "body": json.dumps(body)}

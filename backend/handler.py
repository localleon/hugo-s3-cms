import base64
import json
import io
import boto3
import re
import datetime
from html_sanitizer import Sanitizer
import itertools

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
        return handler_list_directory(event)
    elif req_path.startswith("/get/"):
        return handler_get_file(event)
    elif req_path.startswith("/delete/"):
        return handler_delete_file(event)


def handler_get_file(event):
    """This handler returns the object for the given key"""
    try:
        key = event["pathParameters"]["key"]

        # Get object with key as b64 encoded string and return it
        resp = get_file_from_s3(key)
        if resp[0] == 202:
            return callback(202, {"body": resp[1]})
        else:
            return callback(404, None)

    except KeyError as e:
        return callback(
            401,
            {
                "msg": "Malformed Request. You didn't specify which object should be deleted with a key. Did you provide a valid ressource"
            },
        )


def handler_delete_file(event):
    """This handler deletes a specific object at the given key"""
    try:
        key = event["pathParameters"]["key"]
        # Call the delete s3 function if we got a valid request
        s3_resp = delete_file_from_s3(key)
        return callback(s3_resp[0], s3_resp[1])
    except KeyError as e:
        return callback(
            401,
            {
                "msg": "Malformed Request. You didn't specify which object should be deleted with a key. Did you provide valid json?"
            },
        )


def handler_list_directory(event):
    """This handler returns the keys for all objects in the bucket"""
    try:
        # look if the user requested a page, if not set default page to 1
        page = int(event["queryStringParameters"]["page"], 10)
    except Exception as e:
        page = 1

    objects = list_objects_from_bucket(page)
    return callback(202, {"Contents": objects, "page": page})


def handler_upload_post(event):
    """Upload_post handles the uploading process of the api"""
    body = get_body_from_event(event)

    # Check if request is valid and all fields are filled with content
    if not validate_post_json(body):
        return callback(
            400,
            {
                "msg": "Malformed Request. Not all required json-keys where provided or some fields where left empty"
            },
        )

    # Create an in-memory file and write to aws s3
    filename = get_filename_from_post(body["title"])
    if filename:
        post_file = create_post_file(params=body)
        write_to_s3(file=post_file, filename=filename)
        return callback(200, {"msg": "Post was created successfully"})
    else:
        return callback(400, {"msg": "Title contains illegal characters"})


def get_file_from_s3(key):
    """Get a file from key in our s3 object"""

    # Check if the file really exists before deleting it
    if key not in list_objects_from_bucket():
        return (404, "Key was not found in bucket")

    # trigger the s3 file operation
    buf = io.BytesIO()
    s3.download_fileobj(Bucket=bucket_name, Key=key, Fileobj=buf)
    buf.seek(0)

    # return the file as a base64 encoded string
    return (
        202,
        base64.b64encode(buf.read()).decode(),
    )


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


def list_objects_from_bucket(pageNum):
    # boto3 collections handle pagination for us, we just need to specify the correct page and pagesize
    s3_resp = s3.list_objects_v2(Bucket=bucket_name, Delimiter="/")
    keys = [obj["Key"] for obj in s3_resp["Contents"]]

    pageIndex = calcPagingIndex(pageNum)
    print(f"Returning paged results for {pageIndex} till {pageIndex + 9}")
    return keys[pageIndex : pageIndex + 9]


def calcPagingIndex(pageNum):
    """Calculate the correct indexes for the paging size"""
    pageSize = 8
    return 0 if pageNum == 1 else (pageNum - 1) * pageSize


def get_body_from_event(event):
    return json.loads(event["body"]) if "body" in event.keys() else None


def get_filename_from_post(title):
    """Converts the titel to a filename (cut length at 20),checks if we have safe characters in the path and adds a timestamp"""
    short_title = title.strip().replace(" ", "_")[:20]
    safe_chars = re.compile(
        r"[a-zA-Z0-9.]*$"
    )  # only alphabetic letters and numbers are allowed

    if safe_chars.match(short_title):
        return f"{datetime.date.today().isoformat()}_{short_title}.md"
    else:
        return None


def write_to_s3(file, filename, path=None):
    print(f"Writing to {bucket_name} with {filename} in {path}")
    # construct the s3_key based on if the file should be stored in a folder
    s3_path = path + "/" + filename if path != None else filename

    return s3.upload_fileobj(file, bucket_name, s3_path)


def create_post_file(params):
    """Create_post_file builds a virtual file in memory and returns it"""
    # sanitize the post json for malicious/wrong input
    c_params = sanitize_post_params(params)

    # construct strings for the file
    metadata = f"---\ntitle: {c_params['title']}\ndate: {c_params['date']}\nauthor: {c_params['author']}\ndraft: false\n"
    content = f"---\n{c_params['content']}\n---\n"

    # we create a file in memory, content of markdown needs to be encoded into bytes
    md_file = io.BytesIO()
    md_file.write((metadata + content).encode("UTF-8"))
    md_file.seek(0)

    return md_file


def sanitize_post_params(params):
    """Sanitize the post parameters for malicious html"""
    return {k: Sanitizer().sanitize(v) for k, v in params.items()}


def validate_post_json(params):
    """Tkes the body of the requests and checks if every valid parameter for an upload is filled in"""
    required_keys = ("title", "date", "author", "content")

    # Check if all keys where provided
    provided_keys = [keys in params for keys in required_keys]
    # Check if the metadata and the post content have a valid length
    param_lens = [len(x) > 1 for x in params.values()]

    return all(provided_keys) and all(param_lens)


def callback(status_code, body):
    """Creates a API Gateway compatible response message."""
    return {"statusCode": status_code, "body": json.dumps(body)}

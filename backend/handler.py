import base64
import json
import io
import boto3
import re
import datetime
import bleach

# Config Option -> migrate to env variables
bucket_name = "hugo-cms-store1"
s3 = boto3.client("s3")


def call(x, y):
    return x and y


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

    except KeyError:
        return callback(
            401,
            {
                "msg": "Malformed Request. You didn't specify which object should be accessed with a key. Did you provide a valid ressource?"
            },
        )


def handler_delete_file(event):
    """This handler deletes a specific object at the given key"""
    try:
        key = event["pathParameters"]["key"]
        # Call the delete s3 function if we got a valid request
        s3_resp = delete_file_from_s3(key)
        return callback(s3_resp[0], s3_resp[1])
    except KeyError:
        return callback(
            401,
            {
                "msg": "Malformed Request. You didn't specify which object should be deleted with a key. Did you provide valid json?"
            },
        )


def handler_list_directory(event):
    """This handler returns the keys for all objects in the bucket"""
    try:
        # look if the user requested a page
        page = int(event["queryStringParameters"]["page"], 10)
    except ValueError:
        # if not provied, default value
        page = 1

    objects = list_objects_from_bucket_paged(page)
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
        encode_textfile_to_b64(file_bytes=buf.read()),
    )


def encode_textfile_to_b64(file_bytes):
    """Convert bytes object into utf-8 b64 encoded string"""
    b = base64.b64encode(file_bytes)
    return b.decode("UTF-8")


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


def list_objects_from_bucket():
    """Provides all markdown objects keys from the configured bucket"""
    s3_resp = s3.list_objects_v2(Bucket=bucket_name, Delimiter="/")
    keys = [obj["Key"] for obj in s3_resp["Contents"] if ".md" in obj["Key"]]
    return keys


def list_objects_from_bucket_paged(page_num):
    """Provides an paginated interface for the http-api to get objects keys from the bucket"""
    keys = list_objects_from_bucket()

    # we fake pagination on our api here. The real aws backend is not paginated -> can be implemented using boto3 collections but is complicated
    page_index = calc_paging_index(page_num)
    print(f"Returning paged results for {page_index[0]} till {page_index[1]}")
    return keys[page_index[0] : page_index[1]]


def calc_paging_index(page_num):
    """Calculate the correct indexes for the paging size -> Start with 0, each page should be 8 items"""
    page_size = 8
    if page_num == 1:
        page_start = 0
        return (page_start, page_size - 1)
    else:
        page_start = (page_num - 1) * page_size
        return (page_start, page_start + page_size - 1)


def get_body_from_event(event):
    try:
        # check if we have an actuall body and return safely
        if "body" in event.keys():
            body = json.loads(event["body"])
            return body
        else:
            return None
    except AttributeError:
        # we didn't get a valid aws event -> no dict provided
        return None


def get_filename_from_post(title):
    """Converts the titel to a filename (cut length at 20),checks if we have safe characters in the path and adds a timestamp"""
    title = title.strip()
    safe_chars = re.compile(
        r"[a-zA-Z0-9\-\s.]*$"
    )  # only alphabetic letters and numbers are allowed

    if safe_chars.match(title):
        short_title = title.replace(" ", "_")[:20]
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
    return {k: bleach.clean(v) for k, v in params.items()}


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

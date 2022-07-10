import base64
import json
import io
import boto3
import botocore
import re
import datetime
import bleach


def main_handler(event, context):
    """main_handler handles the internal routing and function calls of the backend based on AWS Events"""
    print("Lambda function ARN:", context.invoked_function_arn)
    print(event)

    # Prepare Execution and extract  Event/Context -> We set the current user fold to the authenticated jwt token subject
    user_dir = get_jwt_token_sub(event)
    init_s3(user_dir)

    # Routing inside the lambda function, we don't need multiple lambda functions for our api
    req_path = event["rawPath"]
    if req_path == "/upload":
        return handler_upload_post(event)
    elif req_path == "/list":
        return handler_list_directory(event)
    elif req_path.startswith("/get/"):
        return handler_get_file(event)
    elif req_path.startswith("/delete/"):
        return handler_delete_file(event)

    # Catch all Error Handler
    return callback(501, {"msg": "Internal Server Error while routing request"})


def init_s3(user_context_dir):
    # Setup S3 Connection and change to correct user directory
    # Config Option -> migrate to env variables
    global s3, bucket_name, user_dir
    bucket_name = "hugo-cms-store1"
    s3 = boto3.client("s3")

    user_dir = user_context_dir


def handler_get_file(event):
    """This handler returns the object for the given key"""
    try:
        key = event["pathParameters"]["key"]

        # Check if the key is not using delimiters aka trying to get files outside user dir
        if not valid_object_key(key):
            return callback(405, {"msg": "Illegal Character found in object key."})

        # Get object with key as b64 encoded string and return it
        b64_file = get_file_from_s3(key)
        if b64_file:
            return callback(202, {"body": b64_file})
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

        if s3_resp == 204:
            return callback(202, {"msg": "Successfully deleted your file!"})
        elif s3_resp == 404:
            return callback(404, {"msg": "Key not found or illegal key!"})
        else:
            return callback(
                501, {"msg": "Internal server error while trying to delete your file"}
            )

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
                "msg": "Malformed Request. Not all required json-keys where provided or other fields where left empty"
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
    # trigger the s3 file operation
    buf = io.BytesIO()

    try:
        s3.download_fileobj(Bucket=bucket_name, Key=f"{user_dir}/{key}", Fileobj=buf)
        buf.seek(0)
        # return the file as a base64 encoded string
        return encode_textfile_to_b64(file_bytes=buf.read())
    except botocore.exceptions.ClientError:
        return None


def encode_textfile_to_b64(file_bytes):
    """Convert bytes object into utf-8 b64 encoded string"""
    b = base64.b64encode(file_bytes)
    return b.decode("UTF-8")


def delete_file_from_s3(key):
    """Delete a file from key in our s3 object and form a correct http response"""
    # Check if the key is valid and if key exists
    if not valid_object_key(key) or key not in list_objects_from_bucket():
        return 404

    # add user_dir to key and trigger the s3 file operation
    s3_resp = s3.delete_object(Bucket=bucket_name, Key=f"{user_dir}/{key}")
    return s3_resp["ResponseMetadata"]["HTTPStatusCode"]


def list_objects_from_bucket():
    """Provides all markdown objects keys from user-specifiy-dir from the configured bucket"""
    s3_resp = s3.list_objects_v2(
        Bucket=bucket_name, Prefix=f"{user_dir}/", Delimiter="/"
    )  # only request keys that belonge to the user

    try:
        keys = [obj["Key"] for obj in s3_resp["Contents"] if ".md" in obj["Key"]]
        return [
            k.replace(f"{user_dir}/", "") for k in keys
        ]  # strip the user_dir from the keys, we don't want to show the user our internal dirs

    except KeyError:
        # triggers if we dont have any "contents" aka object keys in our request
        return []


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
        return (page_start, page_size)
    else:
        page_start = (page_num - 1) * page_size
        return (page_start, page_start + page_size)


def get_body_from_event(event):
    """Extracts HTTP-Body from AWS Event with error handling"""
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
    """Converts the titel to a filename in the user-dir (cut length at 20),checks if we have safe characters in the path and adds a timestamp"""
    title = title.strip()
    safe_chars = re.compile(
        r"[a-zA-Z0-9\-\s.]*$"
    )  # only alphabetic letters and numbers are allowed

    if safe_chars.match(title):
        short_title = title.replace(" ", "_")[:20]

        # add user_dir and timestamp infront of post
        return f"{user_dir}/{datetime.date.today().isoformat()}_{short_title}.md"
    else:
        return None


def write_to_s3(file, filename, path=None):
    """Checks for path existence and performes a file operation"""
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

    try:
        # Check if all keys where provided
        provided_keys = [keys in params for keys in required_keys]
        # Check if the metadata and the post content have a valid length
        param_lens = [len(x) > 1 for x in params.values()]

        return all(provided_keys) and all(param_lens)
    except Exception as e:
        # We didn't get an iterable body aka json
        return False


def valid_object_key(key):
    """Checks for illegal characters in keys (Delimiters and so)"""
    return "/" not in key


def callback(status_code, body):
    """Creates a API Gateway compatible response message."""
    return {"statusCode": status_code, "body": json.dumps(body)}


def get_jwt_token_sub(event):
    """Gets the subject from the verfied jwt token -> user_id"""
    try:
        return event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    except KeyError:
        print("Error: AWS Event contains no subject in jwt token")
        return

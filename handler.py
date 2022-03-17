import json
import io
import boto3
import datetime

# Config Option -> migrate to env variables
bucket_name = "hugo-cms-store1"
s3 = boto3.client("s3")


def upload_post(event, context):
    """Upload_post handles the uploading process of the api"""

    post_params = json.loads(event["body"])

    # Check if request is valid
    if not validate_params(post_params):
        response = {"statusCode": 400, "body": "Not all required keys where provided"}
        return response

    # Create an in-memory file and write to aws s3
    post_file = create_post_file(params=post_params)
    write_to_s3(file=post_file, filename=get_filename_from_post(post_params["title"]))

    # We created the post in the s3 bucket
    response = {"statusCode": 200, "body": "Post was created successfully"}
    return response


def get_filename_from_post(title):
    """Converts the titel to a filename (cut length at 20) and adds a timestamp"""
    short_title = title.replace(" ", "_")[:20]
    return f"{datetime.date.today().isoformat()}_{short_title}.md"


def write_to_s3(file, filename, path=None):
    print(f"Writing to {bucket_name} with {filename} in {path}")
    # construct the s3_key based on if the file should be stored in a folder
    s3_path = path + "/" + filename if path != None else filename

    s3.upload_fileobj(file, bucket_name, s3_path)


def create_post_file(params):
    """Create_post_file builds a virtual file in memory and returns it"""
    metadata = f"---\ntitle: {params['title']}\ndate: {params['date']}\nauthor: {params['author']}\ndraft: false\n"
    content = f"---\n{params['content']}\n---\n"

    # content of markdown needs to be encoded into bytes
    md_file = io.BytesIO()
    md_file.write((metadata + content).encode("UTF-8"))

    md_file.seek(0)
    return md_file


def validate_params(params):
    """Tkes the body of the requests and checks if every valid parameter for an upload is filled in"""
    required_keys = ("title", "date", "author", "content")
    return all(keys in params for keys in required_keys)

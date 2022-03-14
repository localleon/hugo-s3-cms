import json
import io
import boto3


def upload_post(event, context):
    # upload_post handles the uploading process of the api
    post_params = json.loads(event["body"])

    # Check if request is valid
    if not validate_params(post_params):
        response = {"statusCode": 400, "body": "Not all required keys where provided"}
        return response

    # Create an in-memory file and write to aws s3
    post_file = create_post_file(params=post_params)

    # We created the post in the s3 bucket
    response = {"statusCode": 200, "body": "Post was created successfully"}
    return response


def write_to_s3(file, path):
    s3 = boto3.client("s3")


def create_post_file(params):
    md_file = io.StringIO()
    # metadata section
    md_file.write("---\n")
    md_file.write(f"title: {params['title']}\n")
    md_file.write(f"date: {params['date']}\n")
    md_file.write(f"author: {params['author']}\n")
    md_file.write("draft: false\n")

    # Content section
    md_file.write("---\n")
    md_file.write(f'{params["content"]}\n')
    md_file.write("---\n")

    md_file.seek(0)
    return md_file


def validate_params(params):
    # validate_params takes the body of the requests and checks if every valid parameter for an upload is filled in
    required_keys = ("title", "date", "author", "content")
    return all(keys in params for keys in required_keys)

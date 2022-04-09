# hugo-s3-cms 
This project is part of an exam at FOM in the module "Web-Technologien". It's only published for eductional purposes.

hugo-s3-cms is a simple application for uploading markdown files into an s3-storage. We can use it to receive posts for our static hugo-websites and inject them into their build pipeline.

## Login 
Refere to the documentation pdf file for credentials.

## AWS Infrastructure 

The following access points are reachable over the public internet: 
- Backend =  https://85tpt5asaa.execute-api.eu-central-1.amazonaws.com/
- Frontend = https://daq8101a8qkhh.cloudfront.net/index.html

## Local Testing / Invoking 
Use the following commands for local testing. You need to have the AWS Credentials with Bucket Access configured locally.
```
serverless invoke local -f main -e BUCKET_NAME=hugo-cms-store1 --path sample_events/get.json
serverless invoke local -f main -e BUCKET_NAME=hugo-cms-store1 --path sample_events/delete.json
serverless invoke local -f main -e BUCKET_NAME=hugo-cms-store1 --path sample_events/list.json
serverless invoke local -f main -e BUCKET_NAME=hugo-cms-store1 --path sample_events/post.json
```

## Dev Enviroment Setup 
Install requirements (you can decide to make a virtualenv beforhand for python)

```
node -g install serverless 
serverless plugin install -n serverless-python-requirements
pip install -r requirements.txt
pip install -r requirements-dev.txt
```
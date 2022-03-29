# hugo-s3-cms 

hugo-s3-cms is a simple CMS for uploading markdown files into an Object Storage. This readme is not a documentation, it's only used as a note for the dev.

## ToDos 
- Projektbericht schreiben
- CodeReview
  - JS 
  - Python
  - HTML / CSS
- Unit-Tests 
- Erweiterungsmöglichkeiten
  - WYSIWYG Editor einfügen
- UX 
  - Markdown-Preview in der Höhe Begrenzen und mit Scrollbar versehen



## Herausforderungen
- XSS 
- Paging 
- Layout Grid von Ordnern

## AWS Infrastructure 

The following access points are reachable over the public internet: 
- hugo-cms-dev =  https://85tpt5asaa.execute-api.eu-central-1.amazonaws.com/
- hugo-cms-site = https://daq8101a8qkhh.cloudfront.net/index.html


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

```
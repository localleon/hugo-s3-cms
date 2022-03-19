# hugo-s3-cms 

## AWS Infrastructure 


The following access points are reachable over the public internet: 
- hugo-cms-dev =  https://85tpt5asaa.execute-api.eu-central-1.amazonaws.com/
- hugo-cms-site = http://hugo-cms-site.s3-website.eu-central-1.amazonaws.com/index.html
- hugo-cms-store1 = No Public Access Point


## Dev Enviroment Setup 

Install requirements (you can decide to make a virtualenv beforhand for python)
```
node -g install serverless 
serverless plugin install -n serverless-python-requirements
pip install -r requirements.txt

```

Invoke Function locally for testing purposes
```
serverless invoke local -f main --path ./data.json
```
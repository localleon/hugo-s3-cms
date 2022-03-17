# hugo-s3-cms 

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
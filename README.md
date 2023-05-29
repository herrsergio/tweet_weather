# Tweet Weather

```
export AWS_ACCESS_KEY_ID=XXX
export AWS_SECRET_ACCESS_KEY=XXX
cd tweet_weather
python -m venv /tmp/myenv
source /tmp/myenv/bin/activate
pip install pipreqs
python3 -m  pipreqs.pipreqs .
serverless plugin install -n serverless-python-requirements
sls deploy
```

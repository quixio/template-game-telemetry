import os
import redis
import datetime
import json
from flask import Flask, request, Response, render_template_string
from waitress import serve

from setup_logging import get_logger

from quixstreams import Application

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

quix_app = Application()
topic =  quix_app.topic(os.environ["output"])
producer = quix_app.get_producer()

logger = get_logger()

app = Flask(__name__)

# Connect to Redis
client = redis.Redis(host='redis', port=6379, decode_responses=True)


@app.route('/')
def index():
    # Get all keys from Redis
    keys = client.keys('*')
    values = {key: client.get(key) for key in keys}
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Redis Values</title>
        </head>
        <body>
            <h1>Redis Values</h1>
            <ul>
                {% for key, value in values.items() %}
                    <li><strong>{{ key }}:</strong> {{ value }}</li>
                {% endfor %}
            </ul>
        </body>
        </html>
    ''', values=values)


if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=80)
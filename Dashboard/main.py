from flask import Flask, render_template
import redis
import json
from datetime import datetime

app = Flask(__name__)

# Connect to Redis
client = redis.Redis(host='redis', port=6379, decode_responses=True)

@app.route('/')
def index():
    # Get all keys from Redis
    keys = client.keys('*')
    
    # Get game_score items
    game_scores = {key: json.loads(client.get(key)) for key in keys if key.startswith('game_score')}
    
    # Get is_bot items (do nothing with them for now)
    is_bot_flags = {key.split(':')[1]: int(client.get(key)) for key in keys if key.startswith('is_bot')}
    
    # Function to extract is_bot value for a specific GUID
    def get_is_bot_value(guid):
        key = f"b'{guid}'"
        return is_bot_flags.get(key, None)  

    # Add is_bot flag to game_scores
    for key, value in game_scores.items():
        guid = value['game_id']
        is_bot_key = f"b'{guid}'"
        value['is_bot'] = is_bot_flags.get(is_bot_key, 0)
        value['date_time'] = datetime.fromtimestamp(value['timestamp']).strftime('%Y-%m-%d %H:%M:%S')

    # Sort game_scores by timestamp in descending order
    game_scores = dict(sorted(game_scores.items(), key=lambda item: item[1]['timestamp'], reverse=True))

    # Find the top-scoring non-cheater
    top_non_cheater = None
    for key, value in game_scores.items():
        if value['is_bot'] == 0:
            if top_non_cheater is None or value['score'] > top_non_cheater['score']:
                top_non_cheater = value

    return render_template('index.html', game_scores=game_scores, top_non_cheater=top_non_cheater)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
from flask import Flask, render_template_string
import redis
import json

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

    # Sort game_scores by timestamp in descending order
    game_scores = dict(sorted(game_scores.items(), key=lambda item: item[1]['timestamp'], reverse=True))

    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Admin Dashboard</title>
            <style>
                .cheater {
                    background-color: #ff7b7b;
                    width: fit-content;
                }
            </style>
        </head>
        <body>
            <h1>Admin Dashboard</h1>
            <ul>
                {% for key, value in game_scores.items() %}
                    <li class="{{ 'cheater' if value.is_bot == 1 else '' }}">
                        <strong>Game ID:</strong> {{ value.game_id }} - <strong>Score:</strong> {{ value.score }} - <strong>is_bot:</strong> {{ value.is_bot }}
                    </li>
                {% endfor %}
            </ul>
            <div>
                <p>Next refresh in <span id="countdown">5</span> seconds</p>
                <button id="toggle-refresh" class="refresh-toggle">Disable Auto-Refresh</button>
            </div>
            <script>
                let countdown = 5;
                let autoRefresh = true;
                const countdownElement = document.getElementById('countdown');
                const toggleButton = document.getElementById('toggle-refresh');

                function updateCountdown() {
                    if (autoRefresh) {
                        countdown--;
                        if (countdown <= 0) {
                            location.reload();
                        }
                        countdownElement.textContent = countdown;
                    }
                }

                setInterval(updateCountdown, 1000);

                toggleButton.addEventListener('click', function() {
                    autoRefresh = !autoRefresh;
                    if (autoRefresh) {
                        toggleButton.textContent = 'Disable Auto-Refresh';
                        countdown = 5;
                    } else {
                        toggleButton.textContent = 'Enable Auto-Refresh';
                    }
                });
            </script>
        </body>
        </html>
    ''', game_scores=game_scores)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
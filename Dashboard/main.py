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
        print(key)
        guid = value['game_id']
        is_bot_key = f"b'{guid}'"
        value['is_bot'] = is_bot_flags.get(is_bot_key, 0)
        print(value['is_bot'])


    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Redis Values</title>
            <style>
                .cheater {
                    background-color: red;
                }
            </style>
        </head>
        <body>
            <h1>Redis Values</h1>
            <ul>

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
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
    values = {key: json.loads(client.get(key)) for key in keys}
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Redis Values</title>
            <style>
                .refresh-toggle {
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <h1>Redis Values</h1>
            <ul>
                {% for key, value in values.items() %}
                    <li><strong>Game ID:</strong> {{ value.game_id }} - <strong>Score:</strong> {{ value.score }}</li>
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
    ''', values=values)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
import redis
import json

# Connect to Redis
# client = redis.Redis(host='redis', port=6379, decode_responses=True)
server_url = 'tcp://redis-quix-snakegamebackend-dev.deployments.quix.io'
port = 80 # 6379
client = redis.Redis(host=server_url, port=port, decode_responses=True)

# client.flushdb()


# Get all keys from Redis
keys = client.keys('*')

# Print all keys and their values
for key in keys:
    value = client.get(key)
    try:
        # Try to parse the value as JSON
        value = json.loads(value)
    except json.JSONDecodeError:
        pass  # If it's not JSON, just keep the value as is
    print(f"{key}: {value}")
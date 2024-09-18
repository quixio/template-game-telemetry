import redis
import json

# Connect to Redis
client = redis.Redis(host='redis', port=6379, decode_responses=True)

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
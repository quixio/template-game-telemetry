import redis

def test_redis():
    # Connect to Redis server
    client = redis.Redis(host='localhost', port=6379, db=0)

    # Test setting a key
    client.set('test_key', 'test_value')

    # Test getting the key
    value = client.get('test_key').decode('utf-8')

    # Print the result
    print(f"Value for 'test_key': {value}")

    # Clean up
    client.delete('test_key')

if __name__ == "__main__":
    test_redis()
import os
from quixstreams import Application
from datetime import timedelta

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

app = Application(consumer_group="transformation-v54", auto_offset_reset="earliest")

input_topic = app.topic(os.environ["input"])
output_topic = app.topic(os.environ["output"])

sdf = app.dataframe(input_topic)

def can_process(data):
    return data.get('type') == "apple-eaten"


def initializer(value: dict) -> dict:
    return {
        'id': value['session_id'],
        'score': 0
    }


def reducer(aggregated: dict, value: dict) -> dict:
    score = aggregated['score'] + 1
    return {
        'session_id': value['session_id'],
        'score': score
    }


sdf = (

    # filter to only process data relating to the players score
    sdf.filter(can_process)

    # Define a tumbling window of 10 minutes
    .tumbling_window(timedelta(minutes=10))

    # Create a "reduce" aggregation with "reducer" and "initializer" functions
    .reduce(reducer=reducer, initializer=initializer)

    # Emit results only for closed windows
    .final()
)


# sdf = (
#     sdf.filter(should_skip)
#     # Extract "temperature" value from the message
#     .apply(lambda value: 1)
#     # You can also pass duration_ms as an integer of milliseconds
#     .tumbling_window(duration_ms=5000)
#     # Specify the "sum" aggregate function
#     .sum()
#     # Emit updates for each incoming message
#     .current()
# )

sdf.print()
# sdf.to_topic(output_topic)

if __name__ == "__main__":
    app.run(sdf)
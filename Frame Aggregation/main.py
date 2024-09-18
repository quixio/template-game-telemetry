import os
from quixstreams import Application

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

app = Application(consumer_group="transformation-v1", auto_offset_reset="earliest")

input_topic = app.topic(os.environ["input"])
output_topic = app.topic(os.environ["output"])

sdf = app.dataframe(input_topic)

# Using "reduce()" to calculate multiple aggregates at once
def reducer(agg: dict, current: int):
    aggregated = {
        'min': min(agg['min'], current),
        'max': max(agg['max'], current),
        'count': agg['count'] + 1
    }
    return aggregated

def initializer(current) -> dict:
    return {'min': current, 'max': current, 'count': 1}

window = (
    sdf.tumbling_window(duration_ms=1000)
    .reduce(reducer=reducer, initializer=initializer)
    .final()
)

sdf.print()
sdf.to_topic(output_topic)

if __name__ == "__main__":
    app.run(sdf)

import os
from quixstreams import Application

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

app = Application(consumer_group="transformation-v1", auto_offset_reset="earliest")

input_topic = app.topic(os.environ["input"])
output_topic = app.topic(os.environ["output"])

sdf = app.dataframe(input_topic)

def reducer(agg: dict, current: dict):
    for key, value in current.items():
        if key in agg:
            agg[key] += value
        else:
            agg[key] = value
    return agg

def initializer(current) -> dict:
    return current
    
window = (
    sdf.tumbling_window(duration_ms=5000)
    .reduce(reducer=reducer, initializer=initializer)
    .final()
)

sdf.print()
sdf.to_topic(output_topic)

if __name__ == "__main__":
    app.run(sdf)

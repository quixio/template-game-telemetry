from quixstreams import Application
from datetime import timedelta

app = Application()

input_topic = app.topic("input-topic")
sdf = app.dataframe(input_topic)
sdf = (
    sdf.tumbling_window(duration_ms=timedelta(minutes=1))
    .aggregate(lambda df: df.to_json(orient='records'))  # Combine data into JSON format
    .final()
)

sdf.print()

app.run(sdf)
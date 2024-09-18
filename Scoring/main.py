import os
from quixstreams import Application, State

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

app = Application(consumer_group='transformation-v54', auto_offset_reset='earliest')

input_topic = app.topic(os.environ['input'])
output_topic = app.topic(os.environ['output'])

sdf = app.dataframe(input_topic)

def can_process(data):
    return data.get('type') and data.get('snakeLength')

sdf = sdf.filter(can_process)

def calc_score(data: dict, state: State):
    score = state.get('score', 0)
    if data['type'] == 'apple-eaten':
        score += 1
    state.set('score', score)
    data['score'] = score

sdf = sdf.update(calc_score, stateful=True)

def score_json(rows):
    data = {
        'score': rows['score'],
        'length': rows['snakeLength']
    }
    return data

sdf = sdf.apply(score_json)
sdf = sdf.update(lambda row: print(row))

sdf.to_topic(output_topic)

if __name__ == '__main__':
    app.run(sdf)
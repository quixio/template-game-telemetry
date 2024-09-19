import os
import datetime
from quixstreams import Application, State
from sklearn.preprocessing import StandardScaler, LabelEncoder
import pandas as pd
import numpy as np
import boto3
import joblib  # or use pickle if you prefer

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

# Step 1: Download the model from S3
def download_from_s3(bucket_name, s3_file, local_file):
    s3 = boto3.client('s3')
    
    try:
        # Download the file from S3
        s3.download_file(bucket_name, s3_file, local_file)
        print(f"Model downloaded from S3 bucket '{bucket_name}' as '{local_file}'")
    except Exception as e:
        print(f"Error downloading the file: {e}")

# Replace with your bucket name, S3 file name, and local file name
bucket_name = 'quix-pc1hsusp59yhbmbszrpaz3epcjtp1eun1a-s3alias'
s3_file_name = 'bot_detection_0.41.pkl'  # The file stored in S3

# Download the model from S3
download_from_s3(bucket_name, s3_file_name, s3_file_name)

# Step 2: Unpickle (load) the model
def load_model(local_file):
    try:
        # Load the model using joblib (or use pickle if you saved it with pickle)
        model = joblib.load(local_file)
        print("Model loaded successfully.")
        return model
    except Exception as e:
        print(f"Error loading the model: {e}")
        return None

# Load the downloaded model
loaded_model = load_model(s3_file_name)

# Now you can use `loaded_model` for predictions or further tasks
# Example: predictions = loaded_model.predict(X_test)


app = Application(consumer_group="bot-detection-dev-v0.4", auto_offset_reset="earliest")

input_topic = app.topic(os.environ["input"])
output_topic = app.topic(os.environ["output"])

sdf = app.dataframe(input_topic)


sdf["timestamp"] = sdf.apply(lambda row, key, timestamp, _: timestamp, metadata=True)

def fillna(row: dict, column: str):
    
    if column not in row:
        row[column] = np.nan
    
    return row

sdf = sdf.apply(lambda row: fillna(row, column="reason"))
# sdf = sdf.apply(lambda row: fillna(row, column="x"))
# sdf = sdf.apply(lambda row: fillna(row, column="y"))


# Function to extract features from each window
def extract_features(window):
    features = {}

     # Existing features
    event_count = len(window)
    keypress_count = (window['type'] == 'keypress').sum()
    movement_count = (window['type'] == 'movement').sum()
    collision_count = (window['reason'] == 'collision').sum()



    # New ratio features
    # Avoid division by zero by adding a small epsilon (or handling zero cases)
    epsilon = 1e-6  # Small constant to prevent division by zero

    # Ratio of keypress events to movement events
    features['keypress_to_movement_ratio'] = keypress_count / (movement_count + epsilon)

    # Ratio of movement events to total events
    features['movement_to_total_events_ratio'] = movement_count / (event_count + epsilon)

    # Ratio of keypress events to total events
    features['keypress_to_total_events_ratio'] = keypress_count / (event_count + epsilon)

    features['mean_time_delta'] =  window.index.to_series().diff().dt.total_seconds().mean()
    features['std_time_delta'] =  window.index.to_series().diff().dt.total_seconds().std()


    # New reaction time features
    # Calculate reaction times between keypress and movement events
    reaction_times = []
    events = window.reset_index()
    events = events[['timestamp', 'type']]
    
    # Create a list of indices for keypresses and movements
    keypress_indices = events.index[events['type'] == 'keypress'].tolist()
    movement_indices = events.index[events['type'] == 'movement'].tolist()

    # Iterate over keypress indices
    for kp_idx in keypress_indices:
        kp_time = events.loc[kp_idx, 'timestamp']
        
        # Initialize reaction time as NaN
        reaction_time = np.nan
        
        # Search for the closest movement event (before or after)
        # Check the next movement event
        future_movements = [idx for idx in movement_indices if idx >= kp_idx]
        if future_movements:
            mv_idx = future_movements[0]
            mv_time = events.loc[mv_idx, 'timestamp']
            reaction_time = (mv_time - kp_time).total_seconds()
        else:
            # If no movement event after keypress, check previous movement
            past_movements = [idx for idx in movement_indices if idx < kp_idx]
            if past_movements:
                mv_idx = past_movements[-1]
                mv_time = events.loc[mv_idx, 'timestamp']
                reaction_time = (mv_time - kp_time).total_seconds()
            else:
                # No movement events in session
                reaction_time = np.nan
        
        # Append reaction time
        reaction_times.append(reaction_time)
    
    # Remove NaN values from reaction times
    reaction_times = [rt for rt in reaction_times if not np.isnan(rt)]
    
    # Calculate statistical features of reaction times
    if reaction_times:
        features['mean_reaction_time'] = np.mean(reaction_times)
        features['std_reaction_time'] = np.std(reaction_times)
        features['min_reaction_time'] = np.min(reaction_times)
        features['max_reaction_time'] = np.max(reaction_times)
        features['median_reaction_time'] = np.median(reaction_times)
        features['negative_reaction_time_ratio'] = sum(rt < 0 for rt in reaction_times) / len(reaction_times)
        features['zero_reaction_time_ratio'] = sum(rt == 0 for rt in reaction_times) / len(reaction_times)
    else:
        # If no reaction times were calculated
        features['mean_reaction_time'] = np.nan
        features['std_reaction_time'] = np.nan
        features['min_reaction_time'] = np.nan
        features['max_reaction_time'] = np.nan
        features['median_reaction_time'] = np.nan
        features['negative_reaction_time_ratio'] = np.nan
        features['zero_reaction_time_ratio'] = np.nan
    
   
     # Calculate session duration in seconds
    session_start_time = window.index[0]
    session_end_time = window.index[-1]
    session_duration = (session_end_time - session_start_time).total_seconds()
    
    # Handle case where session duration is zero or negative
    if session_duration <= 0:
        session_duration = epsilon  # Assign a small value to avoid division by zero or negative duration
    
    # Calculate keypresses per second
    features['keypresses_per_second'] = keypress_count / session_duration

    # Add more features as needed
    return pd.Series(features)


def feature_calc(data):

    if "reason" not in data:
        data["reason"] = ""

    # Convert timestamp to datetime
    data["timestamp"] = pd.to_datetime(data["timestamp"], unit="ms")

    # Sort data by timestamp
    data.sort_values("timestamp", inplace=True)

    # Fill missing values in 'x' and 'y' by forward filling
    #data["x"] = data["x"].ffill()
    #data["y"] = data["y"].ffill()

    # Encode categorical variables
    event_type_encoder = LabelEncoder()
    data["type_encoded"] = event_type_encoder.fit_transform(data["type"].astype(str))

    reason_encoder = LabelEncoder()
    data["reason_encoded"] = reason_encoder.fit_transform(data["reason"].astype(str))

    # Group data into time windows per session
    data.set_index("timestamp", inplace=True)

    features = extract_features(data)

    feature_columns = [
        "keypress_to_movement_ratio",
        "movement_to_total_events_ratio",
        "keypress_to_total_events_ratio",
        "mean_time_delta",
        "std_time_delta",
        "mean_reaction_time",
        "std_reaction_time",
        "min_reaction_time",
        "max_reaction_time",
        "median_reaction_time",
        "negative_reaction_time_ratio",
        "zero_reaction_time_ratio",
        "keypresses_per_second",
    ]

    result = pd.DataFrame([features])[feature_columns]

    return result


sdf = sdf.hopping_window(60000, 1000).reduce(lambda window, row: window + [row], lambda row: [row]).final()

# Function to predict whether it's a bot
def predict_bot(rows):
    data = pd.DataFrame(rows["value"])
    features_df = feature_calc(data)
    features_array = features_df.values

    # Ensure features_array is a 2D array
    if features_array.ndim == 1:
        features_array = features_array.reshape(1, -1)

    # Handle NaN values
    if np.isnan(features_array).any():
        features_array = np.nan_to_num(features_array)

    # Make prediction
    prediction = loaded_model.predict(features_array)
    return int(prediction[0])  # Convert prediction to int

sdf["is_bot"] = sdf.apply(predict_bot)

def get_session_id(value: dict, key, ts, headers):
    return key

sdf["session_id"] = sdf.apply(get_session_id, metadata=True)

sdf.drop("value")

sdf.print()
sdf.to_topic(output_topic)

if __name__ == "__main__":
    app.run(sdf)

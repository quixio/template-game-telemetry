import os
from flask import Flask, render_template
from pyiceberg.catalog import load_catalog
from azure.storage.blob import BlobServiceClient
from pyiceberg.expressions import EqualTo, And, Or, In
from dotenv import load_dotenv
import pandas as pd
from requests import request
from flask import Flask, render_template, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

app = Flask(__name__)
auth = HTTPBasicAuth()

# Basic auth configuration
users = {
    "admin": generate_password_hash(os.environ["password"])  # Replace with your desired username and password
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None

pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.max_rows', 1000)     # Show all rows
pd.set_option('display.width', 1000)        # Set a wider display width (adjust as needed)
pd.set_option('display.max_colwidth', 100)  # Set maximum column width (optional)

# Initialize Azure Blob Client
container_name = os.environ["AZURE_STORAGE_CONTAINER_NAME"]
blob_service_client = BlobServiceClient.from_connection_string(os.environ["AZURE_STORAGE_CONNECTION_STRING"])
container_client = blob_service_client.get_container_client(container_name)

# Load Iceberg catalog
catalog = load_catalog("sql", uri=os.environ["POSTGRES_CONNECTION_STR"])
namespace = os.environ["NAMESPACE"]
table_name = os.environ["TABLE_NAME"]
base_columns = ["_key", "_timestamp", "channel_name"]


# Generic function to load, filter, and join multiple tables
def load_data(filter_expression, selected_columns):
    dataframes = []
        
    # Load table
    table = catalog.load_table(identifier=f"{namespace}.{table_name}")
    
    # Filter and select columns
    filtered_df = table.scan() \
        .select("*") \
        .to_arrow().to_pandas()
        

    return filtered_df



@app.route('/', methods=['GET', 'POST'])
@auth.login_required
def index():

    if request.method == "GET":

        # Set a default code snippet if custom_code is empty (first load)
        default_code = """# Example transformation code
df = df.set_index("_timestamp")
df = df.resample("50ms").last().reset_index()
df = df[["_timestamp", "vCar:Chassis", "gLat:Chassis"]]
"""
        
        message = "Query data please."


        return render_template('index.html', tables=pd.DataFrame().to_html(classes='data'), titles="Query data", message=message, custom_code=default_code)

    custom_code = default_code if request.method == 'GET' else request.form.get('custom_code', '')

    # Load and join tables
    df = load_data(None, None)

    #df = df.set_index("_timestamp")

    df = df.sort_values(by="_timestamp")

    # Resample to 20 Hz (50 ms intervals) and apply the last aggregation for each column
    #df = df.sort_values(by="_timestamp").resample("50ms").last().reset_index()

    # Display result
    #print(df[["_timestamp", "vCar:Chassis", "gLat:Chassis"]])


    #if request.method == 'POST':
        
        
        

    # Execute custom code on the DataFrame (note: be cautious with exec() in production!)
    try:
        # Use exec() to execute the code within a dictionary containing `df` as `union_result`
        local_vars = {'df': df}
        exec(custom_code, {}, local_vars)
        # Update union_result with the modified df
        df = local_vars['df']
        message = "Transformation applied successfully."
    except Exception as e:
        message = f"Error applying transformation: {e}"
        df = None

    # Render the result as an HTML table
    if df is not None:
        table_html = df[:500].to_html(classes='data')
    else:
        table_html = ""

    return render_template('index.html', tables=table_html, titles=df.columns.values if df is not None else [], message=message, custom_code=custom_code)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=80)
import os
from flask import Flask, render_template, request, redirect
from ibmcloudant.cloudant_v1 import CloudantV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

app = Flask(__name__)

# 1. Connect to IBM Cloudant Database using Cloud Environment Variables
CLOUDANT_URL = os.environ.get("CLOUDANT_URL")
CLOUDANT_APIKEY = os.environ.get("CLOUDANT_APIKEY")
DB_NAME = "cloudkeep-db"

# Fallback for local testing if cloud credentials aren't plugged in yet
tasks_mock_db = []

def get_db_client():
    if CLOUDANT_URL and CLOUDANT_APIKEY:
        authenticator = IAMAuthenticator(CLOUDANT_APIKEY)
        client = CloudantV1(authenticator=authenticator)
        client.set_service_url(CLOUDANT_URL)
        return client
    return None

# 2. Main Page Route
@app.route('/')
def index():
    client = get_db_client()
    if client:
        try:
            # Fetch data from live IBM Cloudant
            response = client.post_all_docs(db=DB_NAME, include_docs=True).get_result()
            tasks = [row['doc'] for row in response['rows'] if 'task' in row['doc']]
            return render_template('index.html', tasks=tasks)
        except Exception:
            # Auto-create database if it doesn't exist yet on IBM Cloud
            client.put_database(db=DB_NAME)
            return render_template('index.html', tasks=[])
    
    # Local fallback view
    return render_template('index.html', tasks=tasks_mock_db)

# 3. Handle Form Submission Route
@app.route('/add', methods=['POST'])
def add_task():
    task_text = request.form.get('task')
    client = get_db_client()
    
    if client:
        # Save directly to live IBM Cloudant
        doc = {"task": task_text}
        client.post_document(db=DB_NAME, document=doc)
    else:
        # Save locally
        tasks_mock_db.append({"task": task_text})
        
    return redirect('/')

if __name__ == '__main__':
    # Bind to the PORT variable assigned by IBM Cloud, default to 8080 locally
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

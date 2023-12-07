from flask import Flask, request, jsonify
from flask_cors import CORS
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import openai
import os

openai.api_key = os.getenv("AZURE_OPENAI_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT") # your endpoint should look like the following https://YOUR_RESOURCE_NAME.openai.azure.com/
openai.api_type = 'azure'
openai.api_version = '2023-07-01-preview' # this may change in the future

# Replace these variables with your Azure Storage account details
account_name = os.getenv("STRG_ACCOUNT_NAME")
account_key = os.getenv("STRG_ACCOUNT_KEY")
container_name = 'output-content'

deployment_name='gpt35' #This will correspond to the custom name you chose for your deployment when you deployed a model. 


app = Flask(__name__)
CORS(app) 

@app.route('/list_containers', methods=['GET'])
def list_containers():
    try:
        blob_service_client = BlobServiceClient(account_url=f"https://{account_name}.blob.core.windows.net", credential=account_key)
        containers = [container.name for container in blob_service_client.list_containers()]
        return jsonify({'containers': containers}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/list_blobs', methods=['GET'])
def list_blobs():
    try:
        blob_service_client = BlobServiceClient(account_url=f"https://{account_name}.blob.core.windows.net", credential=account_key)
        container_client = blob_service_client.get_container_client(container_name)
        max_results = int(request.args.get('max_results', 50))  # Default to 10 if not specified

        blobs = [blob.name for blob in container_client.list_blobs()][:max_results]
        return jsonify({'blobs': blobs}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_blob', methods=['GET'])
def get_blob():
    try:
        blob_name = request.args.get('blob_name')

        blob_service_client = BlobServiceClient(account_url=f"https://{account_name}.blob.core.windows.net", credential=account_key)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        blob_content = blob_client.download_blob().readall()
        return jsonify({'blob_content': blob_content.decode('utf-8')}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/explain', methods=['POST'])
def explain():
    try:
        data = request.get_json()
        date = data.get('date')
        text_content = data.get('text_content')

        # Read from prompt.txt
        with open('prompt.txt', 'r') as file:
            additional_prompt = file.read()

        prompt = f'given a video tape from {date} with this text "{text_content}" extracted from the label, what might be on this tape? {additional_prompt}'

        response = openai.ChatCompletion.create(
        engine="gpt35-turbo-latest",
        messages = [{"role":"system","content":"You are an AI assistant that helps understand what is on archived news video tapes"},
                    {"role":"user","content":prompt}],
        temperature=0.7,
        max_tokens=800,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=False)

        return jsonify({'explain': response.choices[0].message.content}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

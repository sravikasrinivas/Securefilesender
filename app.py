import streamlit as st
import json
from google.cloud import storage
import os
import requests
import base64
 
def displayPDF(file):
    # Opening file from file path
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="950" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)
  
def displayImage(file):
    st.image(file)
  
def upload_with_expiration(creds_path, local_file_path, bucket_name, folder_name):
    client = storage.Client.from_service_account_json(creds_path)
    source_blob_name = os.path.basename(local_file_path)
    destination_blob_name = os.path.join(folder_name, source_blob_name)
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_file_path)

def save_to_server(path,name,folder,expiry_time):
    url = "http://3.110.41.171:8099/upload/"
    payload = {
        "name":name,
        "folder":folder,
        "path": path,
        "expiry_time": expiry_time
    }
    response = requests.post(url, json=payload)
    return response.json()

def get_centers_list():
    url = "http://3.110.41.171:8099/centers_list/"
    payload = {
        "name": "",
    }
    response = requests.post(url, json=payload)
    return response.json()

centers_list = get_centers_list()['centers_list']
    
creds_path = "credentials.json"
bucket_name = "xerorx-project-bucket"

st.title("Zerox Business model")
st.write("Enter the information and click the Upload button")

xerox_uid = st.selectbox(label='select the xerox center', options = centers_list, index=0)
user_name = st.text_input("Enter your name")
upload_file = st.file_uploader("Upload File")
expiry_time = st.number_input("Set expiry Time in minutes", min_value=5)
if upload_file:
    with open(upload_file.name, 'wb') as f:
        f.write(upload_file.getbuffer())
    if upload_file.name.split('.')[-1].lower() == 'pdf':
        st.write('Preview')
        displayPDF(os.path.abspath(upload_file.name))
    elif upload_file.name.split('.')[-1].lower() in ['jpg','png','jpeg']:
        st.write('Preview')
        displayImage(os.path.abspath(upload_file.name))
    else:
        with open(upload_file.name, "rb") as file:
            btn = st.download_button(
                    label="Preview file",
                    data=file,
                    file_name=upload_file.name,
                    mime="image/png")
            
if st.button("Upload"):
    if xerox_uid and user_name:
        local_file_path = upload_file.name
        folder_name = xerox_uid
        upload_with_expiration(creds_path, local_file_path, bucket_name, folder_name)
        bucket_path = folder_name + '/' + upload_file.name
        save_to_server(bucket_path,user_name,folder_name,expiry_time)
        os.remove(upload_file.name)
        st.success('Files uploaded to bucket')
    else:
        st.error('Some fileds are missing')
    

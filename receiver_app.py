import streamlit as st
from google.cloud import storage
import os 
import requests 
import qrcode 
import pandas as pd
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import warnings
warnings.filterwarnings("ignore")

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

bucket_name = "xerorx-project-bucket"
creds_path = "credentials.json"

def delete_from_bucket(path):
    url = "http://34.235.211.247:8099/del/"
    payload = {
        "path": path
    }
    response = requests.post(url, json=payload)
    return response.json()

def get_centers_list(name):
    url = "http://34.235.211.247:8099/centers_list/"
    payload = {
        "name": name,
    }
    response = requests.post(url, json=payload)
    return response.json()


def generate_qr_code(username):
    qr = qrcode.QRCode(version=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_H,
                       box_size=10,
                       border=4)
    data = "https://qr-code-9uz4ulbuawk38wn28cjuya.streamlit.app/"
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"{username}.png") 

def get_status_data(name):
    url = "http://34.235.211.247:8099/csv/"
    payload = {
        "folder": name,
    }
    response = requests.post(url, json=payload)
    df = pd.read_json(response.json(), orient='records')
    return df

def print_file_on_printer(pdf_file_path):
    if os.path.exists(pdf_file_path):
        os.startfile(pdf_file_path, 'print')
    else:
        print(f"PDF file not found at {pdf_file_path}")

# import subprocess, sys
# def print_file_on_printer(pdf_file_path):
#     opener = "open" if sys.platform == "darwin" else "xdg-open"
#     subprocess.call([opener, pdf_file_path])

st.title('Receiver Module')
choice = st.sidebar.selectbox("Select type:", ['Login','Signup'])
if choice == 'Login':
    name, authentication_status, username = authenticator.login('Login', 'main')
    if st.session_state["authentication_status"]:
        generate_qr_code(st.session_state['username'])
        get_centers_list(st.session_state["name"])
        st.markdown(f'Welcome **{st.session_state["name"]}**')
        authenticator.logout('Logout', 'sidebar')
        with open(f"{username}.png", "rb") as file:
            btn = st.sidebar.download_button(
                    label="Download qrcode",
                    data=file,
                    file_name=f"{username}_qrcode.png",
                    mime="image/png")
        
        tab1, tab2, tab3 = st.tabs(["Bucket",'Status', "Local"])

        with tab1:
            folder_name = st.session_state["name"]
            # print(folder_name)
            client = storage.Client.from_service_account_json(creds_path)
            os.makedirs(folder_name, exist_ok=True)
            bucket = client.get_bucket(bucket_name)
            blobs = list(bucket.list_blobs(prefix=folder_name+'/'))
            blobs.sort(key=lambda x: x.time_created)

            st.title("GCS File Browser")
            st.write("### Files in your folder")
            file_names = [blob.name for blob in blobs]
            file_names = [i.replace(folder_name+'/','') for i in file_names]
            file_names = [i for i in file_names if i not in os.listdir(folder_name)]
            if file_names:
                selected_files = st.multiselect("Select files to print:", file_names)
                # print(file_names)
                if st.button("List selected files"):
                    for file_name in selected_files:
                        file_name  = f'{folder_name}/' + file_name
                        blob = bucket.blob(file_name)
                        local_file_path = os.path.join(folder_name,file_name.split("/")[-1])
                        blob.download_to_filename(local_file_path)
                        st.write(f"Downloaded {file_name}")
            else:
                st.markdown('**No files to select**')
            
        with tab2:
            df = get_status_data(st.session_state["name"])
            if df.empty:
                st.markdown('**No data to print**')
            else:
                st.dataframe(df[df.columns[:-1]])
        with tab3:
            st.title('Print Selected files')
            
            local_file_name = os.listdir(folder_name)
            if local_file_name:
                print_files = st.selectbox("Select files to print:", local_file_name)
                if st.button('Print'):
                    st.markdown('**File printing started**')
                    print_file_on_printer(os.path.join(st.session_state["name"],print_files))
                    st.markdown('Removing file after printing')
                    bucket_path = folder_name + '/' + print_files
                    delete_from_bucket(bucket_path)
                    os.remove(os.path.join(folder_name,print_files))
            else:
                st.markdown('**No files to select**')
    elif st.session_state["authentication_status"] == False:
            st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] == None:
        st.warning('Please enter your username and password')
else:
    try:
        if authenticator.register_user('Register user', preauthorization=False):
            with open('config.yaml', 'w') as file:
                yaml.dump(config, file, default_flow_style=False)
            st.success('User registered successfully. Now login and download QR code')
            
    except Exception as e:
        st.error(e)
        
#streamlit run receiver_app.py --server.fileWatcherType none


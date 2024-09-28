import argparse
import requests
import os
import zipfile
import tempfile
import logging

logging.basicConfig(level=logging.DEBUG)

def zip_folder(folder_path):
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=folder_path)
                logging.debug(f"Adding file to ZIP: {arcname}")
                zipf.write(file_path, arcname)
    return temp_zip.name

def submit_job(folder_path, job_name, api_url):
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    logging.debug(f"Zipping folder: {folder_path}")
    zip_path = zip_folder(folder_path)
    
    logging.debug(f"Submitting job to: {api_url}")
    with open(zip_path, 'rb') as zip_file:
        files = {
            'folder': ('folder.zip', zip_file, 'application/zip'),
        }
        payload = {
            'job_name': job_name,
        }
        response = requests.post(api_url, files=files, data=payload)
    
    os.remove(zip_path)
    
    if response.status_code == 200:
        print("Job submitted successfully.")
        print(f"Job details: {response.json()}")
    else:
        print("Failed to submit job.")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")

def main():
    parser = argparse.ArgumentParser(description="Submit a job to the Kubernetes cluster.")
    parser.add_argument("folder", help="Path to the folder containing the script, Dockerfile, and data.")
    parser.add_argument("job_name", help="Name of the Kubernetes job.")
    parser.add_argument("--api-url", default="http://localhost:5000/submit", help="API URL to submit the job.")
    args = parser.parse_args()
    
    submit_job(args.folder, args.job_name, args.api_url)

if __name__ == "__main__":
    main()
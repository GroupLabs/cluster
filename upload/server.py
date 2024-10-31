from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import os
import uuid
from kubernetes import client, config
import zipfile
import logging

app = FastAPI()

# Directory where uploaded files will be saved
UPLOAD_DIRECTORY = "/data/uploads"

# Load Kubernetes config
if os.getenv('KUBERNETES_SERVICE_HOST'):
    config.load_incluster_config()
else:
    config.load_kube_config()

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.get('/')
def health():
    return {"status": "healthy"}

def find_dockerfile(upload_path):
    for root, dirs, files in os.walk(upload_path):
        if 'Dockerfile' in files:
            # Get the full path to the Dockerfile
            dockerfile_full_path = os.path.join(root, 'Dockerfile')
            # Compute the relative path from upload_path to the Dockerfile
            dockerfile_relpath = os.path.relpath(dockerfile_full_path, upload_path)
            return dockerfile_relpath
    return None

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    # Generate a unique identifier for each upload
    upload_id = str(uuid.uuid4())
    upload_path = os.path.join(UPLOAD_DIRECTORY, upload_id)

    # Create a directory for this upload
    os.makedirs(upload_path, exist_ok=True)

    # Save the uploaded zip file
    file_location = os.path.join(upload_path, file.filename)
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)

    # Check if the uploaded file is a zip archive
    if zipfile.is_zipfile(file_location):
        # Extract the zip file into the upload_path
        with zipfile.ZipFile(file_location, 'r') as zip_ref:
            zip_ref.extractall(upload_path)
        # Remove the zip file after extraction
        os.remove(file_location)
    else:
        return JSONResponse({"error": "Uploaded file must be a zip archive"}, status_code=400)

    # Log the contents of the uploaded folder
    logging.info("Contents of uploaded folder:")
    for root, dirs, files in os.walk(upload_path):
        level = root.replace(upload_path, '').count(os.sep)
        indent = ' ' * 4 * (level)
        logging.info(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            logging.info(f"{subindent}{f}")

    # Search for the Dockerfile
    dockerfile_relpath = find_dockerfile(upload_path)
    if dockerfile_relpath is None:
        return JSONResponse({"error": "Dockerfile not found in the uploaded files"}, status_code=400)

    # Trigger Kaniko build job
    job_name = f"kaniko-build-{upload_id}"
    create_kaniko_job(job_name, upload_id, dockerfile_relpath)

    return JSONResponse({
        "message": f"File '{file.filename}' uploaded and Kaniko build job '{job_name}' triggered.",
        "upload_id": upload_id
    })

def create_kaniko_job(job_name, upload_id, dockerfile_relpath):
    batch_v1 = client.BatchV1Api()
    context_path = f"/workspace/{upload_id}/"
    registry_address = "docker-registry.default.svc.cluster.local:5000"

    job_manifest = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {"name": job_name},
        "spec": {
            "template": {
                "metadata": {"name": job_name},
                "spec": {
                    "containers": [{
                        "name": "kaniko",
                        "image": "gcr.io/kaniko-project/executor:latest",
                        "args": [
                            f"--dockerfile={dockerfile_relpath}",
                            f"--context={context_path}",
                            f"--destination={registry_address}/{job_name}:latest"
                        ],
                        "volumeMounts": [{
                            "name": "shared-storage",
                            "mountPath": "/workspace"
                        }]
                    }],
                    "restartPolicy": "Never",
                    "volumes": [{
                        "name": "shared-storage",
                        "persistentVolumeClaim": {
                            "claimName": "shared-pvc"
                        }
                    }]
                }
            }
        }
    }

    try:
        batch_v1.create_namespaced_job(namespace="default", body=job_manifest)
        logging.info(f"Kaniko job '{job_name}' created successfully.")
    except client.exceptions.ApiException as e:
        logging.error(f"Exception when creating Kaniko job: {e}")

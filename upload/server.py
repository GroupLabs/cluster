import logging
import os
import tempfile
import uuid
import zipfile
import secrets
import string

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
from kubernetes import client, config

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow specific origin
    allow_credentials=True,  # Allow cookies and credentials
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

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

@app.get("/")
async def health():
    return {"status" : "healthy"}

@app.post("/detect_libs/")
async def detect_libs(file: UploadFile):
    # Ensure uploaded file is a ZIP
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a ZIP archive.")

    # Create a temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save and extract ZIP file
        zip_path = os.path.join(temp_dir, file.filename)
        try:
            with open(zip_path, "wb") as f:
                f.write(await file.read())

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid ZIP file.")

        # Check for required files and analyze them
        required_files = {"Dockerfile"}
        found_files = set()
        target_strings = ["torch", "numpy", "pandas", "tensorflow"]
        string_found = {}

        for root, dirs, files in os.walk(temp_dir):
            found_files.update(files)

            for file_name in required_files.intersection(files):
                file_path = os.path.join(root, file_name)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().lower()
                    string_found[file_name] = {
                        target: target in content for target in target_strings
                    }

        missing_files = required_files - found_files
        if missing_files:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required file(s): {', '.join(missing_files)}"
            )

    return {"results": string_found}

@app.get("/jobs/")
async def list_jobs():
    batch_v1 = client.BatchV1Api()
    core_v1 = client.CoreV1Api()
    try:
        jobs = batch_v1.list_namespaced_job(namespace="default")
        job_list = []
        for job in jobs.items:
            job_status = get_job_status(job, core_v1)
            job_info = {
                "name": job.metadata.name,
                "status": job_status["job_status"],
                "pod_statuses": job_status["pod_statuses"],
                "ttl": job.spec.ttl_seconds_after_finished if job.spec.ttl_seconds_after_finished is not None else -1
            }
            job_list.append(job_info)
        return {"jobs": job_list}
    except client.exceptions.ApiException as e:
        logging.error(f"Exception when listing jobs: {e}")
        raise HTTPException(status_code=500, detail="Error listing jobs.")

def get_job_status(job, core_v1):
    """
    Get the status of a job and its associated pods.
    """
    job_status = "Unknown"
    pod_statuses = []

    # Determine job status from its conditions
    if job.status.conditions:
        for condition in job.status.conditions:
            if condition.type == "Complete" and condition.status == "True":
                job_status = "Completed"
            elif condition.type == "Failed" and condition.status == "True":
                job_status = "Failed"

    # List pods created by this job
    label_selector = f"job-name={job.metadata.name}"
    pods = core_v1.list_namespaced_pod(namespace="default", label_selector=label_selector)

    for pod in pods.items:
        pod_status = pod.status.phase
        if pod.status.container_statuses:
            for container_status in pod.status.container_statuses:
                if container_status.state.waiting:
                    pod_status = container_status.state.waiting.reason
                elif container_status.state.terminated:
                    pod_status = container_status.state.terminated.reason
                elif container_status.state.running:
                    pod_status = "Running"
        pod_statuses.append({"name": pod.metadata.name, "status": pod_status})

    # Update job status based on pod statuses
    if any(pod["status"] == "Running" for pod in pod_statuses):
        job_status = "Running"

    return {"job_status": job_status, "pod_statuses": pod_statuses}

@app.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    job_name: str = Form(...)
):
    # Validate job name
    if not job_name:
        raise HTTPException(status_code=400, detail="Job name is required")

    # Generate a unique identifier for each upload
    upload_id = str(uuid.uuid4())
    upload_path = os.path.join(UPLOAD_DIRECTORY, upload_id)

    # Create a directory for this upload
    os.makedirs(upload_path, exist_ok=True)

    # Save the uploaded zip file
    file_location = os.path.join(upload_path, file.filename)
    try:
        content = await file.read()
        if not content:
            logging.error("Uploaded file is empty.")
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        with open(file_location, "wb") as f:
            f.write(content)
        logging.info(f"File saved at {file_location}")
    except Exception as e:
        logging.error(f"Error saving uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")

    # Check if the uploaded file is a zip archive
    if zipfile.is_zipfile(file_location):
        try:
            with zipfile.ZipFile(file_location, 'r') as zip_ref:
                zip_ref.extractall(upload_path)
            logging.info(f"Zip file extracted to {upload_path}")
            # Remove the zip file after extraction
            os.remove(file_location)
        except Exception as e:
            logging.error(f"Error extracting zip file: {e}")
            raise HTTPException(status_code=500, detail="Failed to extract zip file.")
    else:
        logging.error("Uploaded file is not a valid zip archive.")
        raise HTTPException(status_code=400, detail="Uploaded file must be a zip archive.")

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
        logging.error("Dockerfile not found in the uploaded files.")
        raise HTTPException(status_code=400, detail="Dockerfile not found in the uploaded files.")

    # Trigger Kaniko build job
    kaniko_job_name = f"{job_name}-kaniko-build-{upload_id}"
    create_kaniko_job(kaniko_job_name, upload_id, dockerfile_relpath)

    # After build, create a job to execute the image and store results
    execution_job_name = f"{job_name}-execution-job-{upload_id}"
    create_execution_job(execution_job_name, kaniko_job_name)

    return JSONResponse({
        "message": f"File '{file.filename}' uploaded and execution job '{execution_job_name}' triggered.",
        "upload_id": upload_id,
        "job_name": job_name
    })

def find_dockerfile(upload_path):
    for root, dirs, files in os.walk(upload_path):
        if 'Dockerfile' in files:
            dockerfile_full_path = os.path.join(root, 'Dockerfile')
            dockerfile_relpath = os.path.relpath(dockerfile_full_path, upload_path)
            return dockerfile_relpath
    return None

def create_kaniko_job(job_name: str, upload_id: str, dockerfile_relpath: str):
    batch_v1 = client.BatchV1Api()

    context_path = f"/workspace/{upload_id}"
    registry     = "docker-registry.default.svc.cluster.local:5000"

    kaniko_args = [
        f"--dockerfile={dockerfile_relpath}",
        f"--context={context_path}",
        f"--destination={registry}/{job_name}:latest",
        # tell Kaniko which CA cert to trust
        f"--registry-certificate={registry}=/certs/ca.crt",
    ]

    if os.getenv("KANIKO_INSECURE", "false").lower() == "true":
        kaniko_args += ["--insecure", "--skip-tls-verify"]

    job_manifest = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {"name": job_name},
        "spec": {
            "template": {
                "metadata": {"name": job_name},
                "spec": {
                    "nodeSelector": {
                        "node-role.kubernetes.io/control-plane": ""
                    },
                    "tolerations": [{
                        "key": "node-role.kubernetes.io/control-plane",
                        "operator": "Exists",
                        "effect": "NoSchedule"
                    }],
                    "restartPolicy": "Never",
                    "containers": [{
                        "name": "kaniko",
                        "image": "gcr.io/kaniko-project/executor:latest",
                        "args": kaniko_args,
                        "volumeMounts": [
                            {
                                "name": "shared-storage",
                                "mountPath": "/workspace"
                            },
                            {
                                "name": "ca-certificates",
                                "mountPath": "/certs"
                            }
                        ]
                    }],
                    "volumes": [
                        {
                            "name": "shared-storage",
                            "persistentVolumeClaim": {
                                "claimName": "shared-pvc"
                            }
                        },
                        {
                            "name": "ca-certificates",
                            "configMap": {
                                "name": "ca-cert"
                            }
                        }
                    ]
                }
            }
        }
    }

    try:
        batch_v1.create_namespaced_job(namespace="default", body=job_manifest)
        logging.info(f"Kaniko job '{job_name}' created successfully.")
    except client.exceptions.ApiException as e:
        logging.error(f"Exception when creating Kaniko job: {e}")

def create_execution_job(job_name, image_name):
    batch_v1 = client.BatchV1Api()
    result_path = "/results"
    image_with_registry = f"docker-registry.default.svc.cluster.local:5000/{image_name}:latest"

    job_manifest = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {"name": job_name},
        "spec": {
            "backoffLimit": 1000,
            "template": {
                "metadata": {"name": job_name},
                "spec": {
                    "containers": [{
                        "name": "executor",
                        "image": image_with_registry,
                        "imagePullPolicy": "Always",
                        "volumeMounts": [{
                            "name": "results-storage",
                            "mountPath": result_path  # Directory in container where results are saved
                        }]
                    }],
                    "restartPolicy": "Never",
                    "volumes": [{
                        "name": "results-storage",
                        "persistentVolumeClaim": {
                            "claimName": "results-pvc"
                        }
                    }]
                }
            }
        }
    }

    try:
        batch_v1.create_namespaced_job(namespace="default", body=job_manifest)
        logging.info(f"Execution job '{job_name}' created successfully.")
    except client.exceptions.ApiException as e:
        logging.error(f"Exception when creating execution job: {e}")

@app.get("/jobs/{job_name}/history")
async def get_job_history(job_name: str):
    batch_v1 = client.BatchV1Api()
    core_v1 = client.CoreV1Api()

    namespace = "default"  # Change if your jobs are in a different namespace

    try:
        # Check if the job exists
        job = batch_v1.read_namespaced_job(name=job_name, namespace=namespace)

        # Retrieve events associated with the job
        field_selector = (
            f"involvedObject.kind=Job,"
            f"involvedObject.name={job_name},"
            f"involvedObject.namespace={namespace}"
        )
        events = core_v1.list_namespaced_event(namespace=namespace, field_selector=field_selector)

        # Process events to extract status transitions
        status_history = []
        for event in sorted(events.items, key=lambda e: e.last_timestamp):
            status = parse_event_message(event.message)
            if status:
                status_history.append({
                    "timestamp": event.last_timestamp.isoformat(),
                    "status": status,
                    "message": event.message
                })

        return {"job_name": job_name, "history": status_history}

    except client.exceptions.ApiException as e:
        if e.status == 404:
            logging.error(f"Job '{job_name}' not found in namespace '{namespace}'.")
            raise HTTPException(status_code=404, detail=f"Job '{job_name}' not found.")
        else:
            logging.error(f"Exception when retrieving job history: {e}")
            raise HTTPException(status_code=500, detail="Error retrieving job history.")

def parse_event_message(message: str) -> str:
    if "Created pod" in message:
        return "Created"
    elif "Started container" in message:
        return "Running"
    elif "Successfully pulled image" in message:
        return "Image Pulled"
    elif "Pulling image" in message:
        return "Pulling Image"
    elif "Job completed" in message or "Completed" in message:
        return "Complete"
    elif "Failed" in message or "Error" in message:
        return "Error"
    elif "Back-off" in message:
        return "Back-off"
    else:
        return None

@app.get("/jobs/{job_name}/logs")
async def get_job_logs(job_name: str):
    core_v1 = client.CoreV1Api()
    batch_v1 = client.BatchV1Api()
    namespace = "default"  # Replace with your namespace if different

    try:
        # Get the job to ensure it exists
        job = batch_v1.read_namespaced_job(name=job_name, namespace=namespace)

        # List pods associated with the job
        label_selector = f"job-name={job_name}"
        pods = core_v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)

        if not pods.items:
            raise HTTPException(status_code=404, detail=f"No pods found for job '{job_name}'")

        # Sort pods by creation timestamp to get the last created pod
        pods.items.sort(key=lambda pod: pod.metadata.creation_timestamp, reverse=True)
        last_pod = pods.items[0]

        # Get the logs of the last pod
        pod_name = last_pod.metadata.name
        logs = core_v1.read_namespaced_pod_log(name=pod_name, namespace=namespace)

        return {"job_name": job_name, "pod_name": pod_name, "logs": logs}

    except client.exceptions.ApiException as e:
        if e.status == 404:
            logging.error(f"Job '{job_name}' not found in namespace '{namespace}'.")
            raise HTTPException(status_code=404, detail=f"Job '{job_name}' not found.")
        else:
            logging.error(f"Exception when retrieving logs for job '{job_name}': {e}")
            raise HTTPException(status_code=500, detail="Error retrieving pod logs.")

@app.post("/ephemeral_notebook/")
async def create_ephemeral_notebook(
    session_name: str = Form(...),
    image_name: str = Form(...),
    token: Optional[str] = Form(None),
    ttl_seconds: int = Form(300),  # auto-delete job after 5 minutes of completion
    base_domain: str = Form("notebooks.local")
):
    """
    Creates:
    1) A K8s Job for an ephemeral Jupyter session (with a TTL).
    2) A Service (ClusterIP) to target the Pod.
    3) An Ingress with host-based routing, e.g. <session_name>.<base_domain>.
    """

    if not session_name:
        raise HTTPException(status_code=400, detail="session_name is required")
    if not image_name:
        raise HTTPException(status_code=400, detail="image_name is required")

    # Generate random token if none supplied
    if not token:
        token = generate_random_token(16)

    # Namespaced resources
    namespace = "default"

    # Resource names
    job_name = f"{session_name}-job"
    svc_name = f"{session_name}-svc"
    ingress_name = f"{session_name}-ing"

    # The jupyter notebook port
    notebook_port = 8888

    # The host for this ephemeral notebook, e.g. "my-session.yourdomain.com"
    notebook_host = f"{session_name}.{base_domain}"

    # Step 1: Create ephemeral Job
    try:
        create_jupyter_job(
            job_name=job_name,
            namespace=namespace,
            image_name=image_name,
            token=token,
            port=notebook_port,
            ttl_seconds=ttl_seconds
        )
    except client.exceptions.ApiException as e:
        logging.error(f"Error creating Job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Step 2: Create Service (ClusterIP)
    try:
        create_jupyter_service(
            svc_name=svc_name,
            namespace=namespace,
            job_label=job_name,  # labels the pod with app=job_name
            port=notebook_port
        )
    except client.exceptions.ApiException as e:
        logging.error(f"Error creating Service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Step 3: Create Ingress with host-based routing
    try:
        create_jupyter_ingress(
            ingress_name=ingress_name,
            namespace=namespace,
            svc_name=svc_name,
            port=notebook_port,
            host=notebook_host
        )
    except client.exceptions.ApiException as e:
        logging.error(f"Error creating Ingress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Return the host-based URL
    # If you have TLS, it would be https://
    jupyter_url = f"http://{notebook_host}/?token={token}"

    return {
        "message": "Ephemeral Jupyter notebook created",
        "job_name": job_name,
        "service_name": svc_name,
        "ingress_name": ingress_name,
        "token": token,
        "jupyter_url": jupyter_url
    }

def create_jupyter_job(job_name: str,
                       namespace: str,
                       image_name: str,
                       token: str,
                       port: int,
                       ttl_seconds: int):
    """
    Creates a K8s Job that runs a Jupyter notebook container and sets a TTL
    so it auto-deletes after completion. The user can kill the notebook
    from within or once they close the Pod, it eventually completes.
    """
    batch_v1 = client.BatchV1Api()

    # Command to run Jupyter in ephemeral mode
    command = [
        "jupyter",
        "notebook",
        f"--port={port}",
        "--ip=0.0.0.0",
        "--no-browser",
        "--allow-root",
        f"--NotebookApp.token={token}",
        "--NotebookApp.password=''",
        "--NotebookApp.default_url=/lab"
    ]

    job_manifest = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": job_name
        },
        "spec": {
            "ttlSecondsAfterFinished": ttl_seconds,
            "template": {
                "metadata": {
                    # Label used to select the Pod with the Service.
                    "labels": {
                        "app": job_name
                    }
                },
                "spec": {
                    "restartPolicy": "Never",
                    "containers": [
                        {
                            "name": "jupyter",
                            "image": image_name,
                            "command": command,
                            "ports": [{"containerPort": port}],
                            "resources": {
                                "requests": {"memory": "512Mi", "cpu": "250m"},
                                "limits":   {"memory": "1Gi",  "cpu": "500m"}
                            }
                        }
                    ],
                }
            }
        }
    }
    batch_v1.create_namespaced_job(namespace=namespace, body=job_manifest)
    logging.info(f"Job '{job_name}' created in '{namespace}'")

def create_jupyter_service(svc_name: str,
                           namespace: str,
                           job_label: str,
                           port: int):
    """
    Creates a ClusterIP Service that routes to the Pod labeled app=job_label.
    """
    core_v1 = client.CoreV1Api()

    service_manifest = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": svc_name
        },
        "spec": {
            "type": "ClusterIP",
            "selector": {
                "app": job_label
            },
            "ports": [
                {
                    "port": port,
                    "targetPort": port
                }
            ]
        }
    }

    core_v1.create_namespaced_service(namespace=namespace, body=service_manifest)
    logging.info(f"Service '{svc_name}' created in '{namespace}'")

def create_jupyter_ingress(ingress_name: str,
                           namespace: str,
                           svc_name: str,
                           port: int,
                           host: str):
    """
    Creates an Ingress route on host=<host>, forwarding traffic to the Service <svc_name>:<port>.
    Assumes an Ingress controller (like NGINX) is set up in the cluster.
    TLS configuration or annotations can be added if you want HTTPS.
    """
    networking_v1 = client.NetworkingV1Api()

    # Basic host-based routing, HTTP only for now
    ingress_manifest = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": ingress_name,
            # Add annotations for your specific Ingress controller,
            # e.g., to enable TLS or set custom behaviors.
            # "annotations": {
            #     "kubernetes.io/ingress.class": "nginx",
            #     "cert-manager.io/cluster-issuer": "letsencrypt-prod",
            # }
        },
        "spec": {
            "rules": [
                {
                    "host": host,
                    "http": {
                        "paths": [
                            {
                                "path": "/",     # or "/notebook"
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": svc_name,
                                        "port": {
                                            "number": port
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            ],
            # For HTTPS/TLS, add something like:
            # "tls": [
            #   {
            #     "hosts": [host],
            #     "secretName": "some-tls-secret"
            #   }
            # ]
        }
    }

    networking_v1.create_namespaced_ingress(namespace=namespace, body=ingress_manifest)
    logging.info(f"Ingress '{ingress_name}' created in '{namespace}'")

def generate_random_token(length: int) -> str:
    """
    Generate a cryptographically-secure random token for Jupyter.
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

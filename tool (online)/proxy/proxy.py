from flask import Flask, request, jsonify
import os
from kubernetes import client, config
import zipfile
import logging
import time

app = Flask(__name__)

# Load Kubernetes config
if os.getenv('KUBERNETES_SERVICE_HOST'):
    config.load_incluster_config()
else:
    config.load_kube_config()

@app.route('/')
def health():
    return {"status": "healthy", "start" : start_time}

@app.route('/submit', methods=['POST'])
def submit_job():
    job_name = request.form['job_name']
    
    if 'folder' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['folder']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        # Create a temporary directory to save the uploaded files
        temp_dir = f"/mnt/scripts/{job_name}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save the uploaded ZIP file
        zip_path = os.path.join(temp_dir, 'upload.zip')
        file.save(zip_path)
        
        # Extract the ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        print("Contents of uploaded folder:")
        for root, dirs, files in os.walk(temp_dir):
            level = root.replace(temp_dir, '').count(os.sep)
            indent = ' ' * 4 * (level)
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                print(f"{subindent}{f}")
        
        # Remove the ZIP file after extraction
        os.remove(zip_path)
        
        # Check if Dockerfile exists
        if not os.path.exists(os.path.join(temp_dir, "Dockerfile")):
            return jsonify({'error': 'Dockerfile not found in uploaded files'}), 400
        
        logging.debug(f"Contents of {temp_dir}:")
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                logging.debug(os.path.join(root, file))
        
        # Create Kaniko build job
    build_job_name = f"{job_name}-build"
    image_name = f"{job_name}-image:latest"
    full_image_name = f"registry.default.svc.cluster.local:5000/{image_name}"
    build_job_spec = create_kaniko_job_spec(build_job_name, f"scripts/{job_name}", full_image_name)

    # Submit the Kaniko build Job to the Kubernetes cluster
    batch_v1 = client.BatchV1Api()
    namespace = "default"  # Use appropriate namespace
    build_response = batch_v1.create_namespaced_job(
        body=build_job_spec,
        namespace=namespace
    )

    time.sleep(180)  # Wait for Kaniko job to complete

    # # Wait for Kaniko job to complete
    # while True:
    #     job_status = batch_v1.read_namespaced_job_status(build_job_name, namespace)
    #     if job_status.status.succeeded is not None and job_status.status.succeeded > 0:
    #         print(f"Kaniko job {build_job_name} completed successfully")
    #         break
    #     elif job_status.status.failed is not None and job_status.status.failed > 0:
    #         return jsonify({'error': f'Kaniko job {build_job_name} failed'}), 500
    #     time.sleep(5)  # Wait for 5 seconds before checking again

    # Create the actual job spec
    job_spec = create_job_spec(job_name, f"10.100.219.237:5000/{image_name}")

    # Submit the actual Job to the Kubernetes cluster
    response = batch_v1.create_namespaced_job(
        body=job_spec,
        namespace=namespace
    )

    return jsonify({
        'job_name': job_name,
        'status': 'submitted',
        'build_job': build_response.to_dict(),
        'run_job': response.to_dict()
    })

def create_kaniko_job_spec(job_name, context_dir, image_name):
    container = client.V1Container(
        name="kaniko",
        image="gcr.io/kaniko-project/executor:latest",
        args=[
            "--context=/workspace",
            f"--dockerfile=/workspace/{context_dir}/Dockerfile",
            f"--destination={image_name}",
            "--verbosity=debug",
            "--cache=true",
            "--cache-ttl=24h"
        ],
        volume_mounts=[
            client.V1VolumeMount(
                name="shared-volume",
                mount_path="/workspace"
            ),
            client.V1VolumeMount(
                name="kaniko-cache",
                mount_path="/cache"
            )
        ]
    )

    job_spec = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=job_name),
        spec=client.V1JobSpec(
            template=client.V1PodTemplateSpec(
                spec=client.V1PodSpec(
                    containers=[container],
                    restart_policy="Never",
                    volumes=[
                        client.V1Volume(
                            name="shared-volume",
                            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                                claim_name="example-pvc"
                            )
                        ),
                        client.V1Volume(
                            name="kaniko-cache",
                            empty_dir=client.V1EmptyDirVolumeSource()
                        )
                    ]
                )
            )
        )
    )

    return job_spec

def create_job_spec(job_name, image_name):
    container = client.V1Container(
        name=job_name,
        image=image_name,
        image_pull_policy="Always",
        # command=["/bin/sh", "-c"], # respect the Dockerfile CMD
        # args=[f"python /mnt/scripts/{job_name}/{job_name}.py"],
        volume_mounts=[
            client.V1VolumeMount(
                name="shared-volume",
                mount_path="/mnt"
            )
        ]
    )

    job_spec = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=job_name),
        spec=client.V1JobSpec(
            template=client.V1PodTemplateSpec(
                spec=client.V1PodSpec(
                    service_account_name="job-puller",  # Use the new ServiceAccount
                    containers=[container],
                    restart_policy="Never",
                    volumes=[
                        client.V1Volume(
                            name="shared-volume",
                            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                                claim_name="example-pvc"
                            )
                        )
                    ]
                )
            )
        )
    )
    return job_spec

global start_time
if __name__ == '__main__':
    import datetime
    start_time = str(datetime.datetime.now())
    app.run(host='0.0.0.0', port=5000)
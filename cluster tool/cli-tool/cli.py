import click
import subprocess
import os
import shutil

@click.group()
def cli():
    """Kubernetes Python Script CLI"""
    pass

@cli.command()
@click.argument('script_path')
@click.argument('requirements_path')
def build(script_path, requirements_path):
    """Build Docker image from the Python script and requirements"""
    click.echo("Building Docker image...")
    try:
        # Ensure the files are in the build context
        script_dest = './script.py'
        requirements_dest = './requirements.txt'

        # Copy the files into the current directory (build context)
        shutil.copy(script_path, script_dest)
        shutil.copy(requirements_path, requirements_dest)

        # Create Dockerfile dynamically with relative paths
        dockerfile_content = f"""
FROM python:3.9-slim
WORKDIR /app
COPY script.py /app/script.py
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "-u", "script.py"]
        """

        # Write Dockerfile content to a file
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)

        # Build the Docker image
        subprocess.run(['docker', 'build', '-t', 'python-script:latest', '.'])
        click.echo("Docker image built successfully!")
    except Exception as e:
        click.echo(f"Error: {e}")

@cli.command()
def deploy():
    """Deploy the Docker image as a Kubernetes Job"""
    click.echo("Deploying to Kubernetes...")
    try:
        # Create Kubernetes Job YAML
        job_yaml = """
        apiVersion: batch/v1
        kind: Job
        metadata:
          name: python-script-job
        spec:
          template:
            spec:
              containers:
              - name: python-script
                image: python-script:latest
                imagePullPolicy: Never
              restartPolicy: Never
          backoffLimit: 4
        """
        with open("job.yaml", "w") as f:
            f.write(job_yaml)

        # Deploy the Job
        subprocess.run(['kubectl', 'apply', '-f', 'job.yaml'])
        click.echo("Kubernetes Job deployed successfully!")
    except Exception as e:
        click.echo(f"Error: {e}")

@cli.command()
def status():
    """Check the status of the Kubernetes Job and follow logs in real-time"""
    click.echo("Checking job status and streaming logs...")
    try:
        # Get the job status
        subprocess.run(['kubectl', 'get', 'jobs'])

        # Get the pod name associated with the job
        pod_name = subprocess.check_output(
            ["kubectl", "get", "pods", "--selector=job-name=python-script-job", "--output=jsonpath='{.items[0].metadata.name}'"]
        ).decode('utf-8').strip().strip("'")

        # Stream the logs in real-time
        subprocess.run(['kubectl', 'logs', '-f', f'pod/{pod_name}'])

    except Exception as e:
        click.echo(f"Error: {e}")

if __name__ == '__main__':
    cli()
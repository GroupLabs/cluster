# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Run pip to install any dependencies (if you had a requirements.txt file)
# RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container (if applicable)
# EXPOSE 80

# Run script.py when the container launches
CMD ["python", "script.py"]

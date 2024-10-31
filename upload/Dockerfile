# Dockerfile

FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI application code
COPY server.py .

# Expose port 80
EXPOSE 80

# Start the FastAPI application using Uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "80"]

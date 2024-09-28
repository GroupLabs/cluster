
FROM python:3.9-slim
WORKDIR /app
COPY script.py /app/script.py
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "-u", "script.py"]
        
FROM python:3.8-slim

WORKDIR /app

RUN pip install pandas

COPY . /app

EXPOSE 5000

CMD ["python", "example_script.py"]

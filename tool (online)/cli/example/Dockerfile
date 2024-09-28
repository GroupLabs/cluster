FROM python:3.8-slim

WORKDIR /app/scripts/job17

RUN pip install pandas

COPY . /app

EXPOSE 5000

CMD ["python", "example_script.py"]
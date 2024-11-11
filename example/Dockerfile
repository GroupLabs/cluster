FROM python:3.8-slim

WORKDIR /app

RUN pip install pandas

COPY . /app
RUN ls /app  # Debugging step to confirm files are copied correctly

# Change the working directory to /app/example
WORKDIR /app/example

EXPOSE 5000

# Now you can run the script without specifying the full path
CMD ["python", "example_script.py"]

# Steps to Run the API

1. Run FastAPI: You can run the FastAPI application using `uvicorn`:

``` bash
uvicorn app.main:app --reload
```
This will start the API at `http://127.0.0.1:8000`.

2. Testing the API:

GET Request: `GET /data/` Retrieves the CSV data from Google Drive and returns it as JSON.

POST Request: `POST /data/` Adds a new record to the CSV file on Google Drive. Example usage:

```bash
POST /data/?name=John&age=30
```

## Optional Dockerfile (for containerization)

If you want to deploy this API in a containerized environment, you can use Docker:

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /usr/src/app

# Install the required Python packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Run the FastAPI app using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

## Dependencies

List your dependencies in requirements.txt:

``` text
fastapi
uvicorn
pandas
google-auth
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
pydrive
```
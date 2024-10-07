from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import io
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/drive']

# Load your service account credentials (downloaded JSON file)
SERVICE_ACCOUNT_FILE = 'credentials.json'

def get_drive_service():
    """Create and return a Google Drive service object."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # Create a Drive API service object
    service = build('drive', 'v3', credentials=credentials)
    return service

def download_csv(file_name, folder_id):
    """Download a CSV file from Google Drive using the file ID."""
    service = get_drive_service()
    
    # Query to search for the file by name within the specified folder
    query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and name='{file_name}'"

    # Execute the query
    response = service.files().list(q=query, fields="files(id, name)").execute()
    files = response.get('files', [])

    if not files:
        raise Exception(f"No files found with the name '{file_name}' in the specified folder.")
    
    # Assuming you want the first file found with that name
    file_id = files[0]['id']

    # Now download the file content
    request = service.files().export_media(fileId=file_id, mimeType='text/csv')
    file_stream = io.BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)

    done = False
    while done is False:
        status, done = downloader.next_chunk()

    file_stream.seek(0)
    return io.StringIO(file_stream.read().decode('utf-8'))

def upload_csv(file_name, folder_id, file_id=None):
    """Uploads a CSV file to Google Drive in the specified folder or updates it if file_id is provided."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)

    if file_id:
        # Update the existing file
        file_metadata = {
            'name': file_name.split('/')[-1],  # Use just the file name
            # No need to specify 'parents' here as we are only updating the file itself
        }
        media = MediaFileUpload(file_name, mimetype='text/csv')
        service.files().update(fileId=file_id, body=file_metadata, media_body=media).execute()
        return file_id  # Return the ID of the updated file

    else:
        # Create a new file
        file_metadata = {
            'name': file_name.split('/')[-1],
            'mimeType': 'application/vnd.google-apps.spreadsheet',  # This ensures it is created as a Google Sheet
            'parents': [folder_id]  # Specify the folder ID where the file should be uploaded
        }

        # Upload the file
        media = MediaFileUpload(file_name, mimetype='text/csv')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        return file.get('id')  # Return the ID of the uploaded file

def list_files_in_folder(folder_id):
    """List all files in a specific Google Drive folder."""
    service = get_drive_service()

    # Query to list all files in the specified folder
    query = f"'{folder_id}' in parents"

    # Execute the query
    response = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    files = response.get('files', [])

    if not files:
        return []  # Return an empty list if no files are found

    return files  # Return the list of files found


import os
import pickle

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

from config import SPREADSHEET_ID as SHEET_ID
from config import DOCUMENT_ID as DOC_ID


# Scope for Google Drive access
SCOPES = ['https://www.googleapis.com/auth/drive']


def get_gdrive_service():

    creds = None

    if os.path.exists('token_drive.pickle'):

        with open('token_drive.pickle', 'rb') as file:
            creds = pickle.load(file)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credential_drive.json', SCOPES
            )

            creds = flow.run_local_server(port=0)

        with open('token_drive.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)

    return service


# Step 2: Copy Google Drive File
def copy_drive_file(service, file_id, new_file_name):

    # Check existing file
    document = service.files().get(
        fileId=file_id,
        fields='id,name,mimeType'
    ).execute()

    print("Original File Found:", document['name'])

    # Copy file into Google Drive
    file_metadata = {
        'name': new_file_name
    }

    copied_file = service.files().copy(
        fileId=file_id,
        body=file_metadata,
        fields='id,name,mimeType,webViewLink'
    ).execute()

    print("File copied successfully!")
    print("New File Name:", copied_file['name'])
    print("New File ID:", copied_file['id'])
    print("File Link:", copied_file.get('webViewLink'))

    return copied_file


# Step 3: Main Function
def main_drive():

    try:

        service = get_gdrive_service()

        print("Copying Google Doc...")

        copy_drive_file(
            service,
            DOC_ID,
            'Copied_Google_Document'
        )

        print("\nCopying Google Sheet...")

        copy_drive_file(
            service,
            SHEET_ID,
            'Copied_Google_Sheet'
        )

        print("Both files copied successfully to Google Drive!")

    except HttpError as error:

        print("Google Drive API Error:", error)


if __name__ == '__main__':
    main_drive()
  
import os.path
# from test_api import getEmails
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES=["https://www.googleapis.com/auth/documents"]

# The ID of a sample document.
DOCUMENT_ID="1nUZlsajgmMTLmfUFgnpgngTzyt-o3rUv8BLyod8YQSc"

def get_service():
  """Shows basic usage of the Docs API.
  Prints the title of a sample document.
  """

  creds=None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds=Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow=InstalledAppFlow.from_client_secrets_file(
          "client_secret_466515381639-02j4a781scu5f4gl1o8lspum11tp7qms.apps.googleusercontent.com.json", SCOPES
      )
      creds=flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service=build("docs", "v1", credentials=creds)
    return service
  except HttpError as err:
    print(err)

def main(email_body):
  if len(email_body)==0:
    return "No data to insert!"
  
  try:
    service=get_service()
    for i in email_body:

      # Retrieve the documents contents from the Docs service.
      # document1=service.documents().get(documentId=DOCUMENT_ID).execute()
      requests=[
          {
              "insertText": {
                  "location": {"index": 1},
                  "text": f'{i['id']} | {i['name']} | {i['dob']} | {i['email_id']} | {i['age']} \n'
              }
          }
      ]

      result=service.documents().batchUpdate(
          documentId=DOCUMENT_ID,
          body={"requests": requests}
      ).execute()

    print("Update applied:", result)
    # print(f"The title of the document is: {document1.get('title')}")
  except HttpError as err:
    print(err)
  
if __name__ == "__main__":
  # email_body=getEmails()
  main()
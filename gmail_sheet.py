import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
 
 
 
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
 
 
# the id of the sheet you want to access
SPREADSHEET_ID ="1BhEtjWktx3ypTdMclMNWH_YsHUGED7qprOxlwuwZgII"
RANGE_NAME = "Sheet1!A2:D"
 
def get_creds():
  creds=None
 
  if os.path.exists("token_sheet.json"):
    creds =Credentials.from_authorized_user_file("token_sheet.json",SCOPES)
 
  if not creds or not creds.valid:
    # if creds are present and it is expired and refresh token is available
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      # get creds and write it to token.json
      flow =InstalledAppFlow.from_client_secrets_file("credential_sheet.json",SCOPES)
      creds =flow.run_local_server(port=0)
 
    with open("token_sheet.json","w") as token:
      token.write(creds.to_json())
 
  return creds
 
 
def get_value():
  service =build("sheets","v4",credentials=get_creds())
  sheet =service.spreadsheets()
  result =(sheet.values().get(spreadsheetId=SPREADSHEET_ID,range=RANGE_NAME).execute())
  values =result.get("values", [])
  return values
 
 
def write_in_sheet(value_input_option):
  try:
    #   with open("agecalculated_data.json", "r", encoding="utf-8") as file:
        #   data = json.load(file)
          # print(data)
 
      # fetch the list of dectionary
    #   data = suraj_function()
        data=[{
        "id":"2",
        "name":"chaitanya",
        "dob":"20-12-2004",
        "email":"dusane7263@gmail.com",
        "age":"23"
        },
        {
        "id":"3",
        "name":"akhilesh",
        "dob":"07-06-2004",
        "email":"akhileshi7263@gmail.com",
        "age":"62"
        }]
 
 
        headers = ["id", "name", "dob", "email","age"]
     
        values =[]
        for item in data:
            row = [item.get(col,"") for col in headers]
            
            values.append(row)
    
        body ={"values": values}
        service =build("sheets","v4",credentials=get_creds())
        result = (service.spreadsheets().values().append(spreadsheetId=SPREADSHEET_ID,range=RANGE_NAME,
                    valueInputOption=value_input_option,body=body,).execute())
        print(f"{(result.get('updates').get('updatedCells'))} cells appended.")
        return result
    #   return result.get("spreadsheetId")
 
  except HttpError as error:
      print(f"An error occurred: {error}")
      return error
 
 
def main():
  try:
    values=get_value()
    if not values:
      print("No data found.")
      return
    print("Name, ID, DOB:")
    for row in values:
        print(row)
  except HttpError as err:
    print(err)
if __name__ == "__main__":
  # main()
  write_in_sheet("USER_ENTERED")
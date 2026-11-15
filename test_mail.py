import base64
import os
from datetime import date,datetime
from email.mime.text import MIMEText
from email.utils import parseaddr
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

scopes = ["https://www.googleapis.com/auth/gmail.send","https://www.googleapis.com/auth/gmail.modify"]
credentials_file = "credential_mail.json"
token_file = "token_mail.json"
search_subject = "Batch-2026"
header = ["id","name","DD/MM/YYYY","email_id"]
headers_with_age =header+["age"]

def get_gmail_service():
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file,scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file,scopes)
            creds = flow.run_local_server(port=0)
        with open(token_file,"w") as f:
            f.write(creds.to_json())
    return build("gmail","v1",credentials=creds)

def valid_date(s):
    try:
        datetime.strptime(s,"%d/%m/%Y")
        return True
    except ValueError:
        return False

def calculate_age(dob_text,today=None):
    today = today or date.today()
    dob = datetime.strptime(dob_text,"%d/%m/%Y").date()
    age = today.year - dob.year
    if (today.month,today.day) <(dob.month,dob.day):
        age =age-1
    return age

def add_age(rows):
    return [r +[calculate_age(r[2])] for r in rows]

def make_table(rows, headers=header):
    data = [headers] + rows
    n = len(headers)
    widths = [max(len(str(r[i])) for r in data) for i in range(n)]
    lines = [" | ".join(str(c).ljust(widths[i]) for i,c in enumerate(r)) for r in data]
    return "\n".join(lines)

def parse_table(text):
    rows = []
    for line in text.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 4 and valid_date(parts[2]):
            if parts not in rows:  # skip duplicates
                rows.append(parts)
    return rows

def rows_to_dicts(rows):
    return [{"id": r[0], "name": r[1], "dob": r[2], "email_id": r[3], "age": str(r[4])}
            for r in rows]

def send_mail(gmail,to,subject,body,thread_id=None,in_reply_to=None):
    msg = MIMEText(body,"plain")
    msg["To"] =to
    msg["Subject"] =subject
    if in_reply_to:
        msg["In-Reply-To"] =in_reply_to
        msg["References"] =in_reply_to
    payload = {"raw":base64.urlsafe_b64encode(msg.as_bytes()).decode()}
    if thread_id:
        payload["threadId"] = thread_id
    return gmail.users().messages().send(userId="me",body=payload).execute()

def send_employee_email(gmail,rows,to,subject="Employee Details"):
    body = make_table(rows)
    return send_mail(gmail,to,subject,body)

def send_flow(gmail):
    rows = []
    print("\nEnter employees (leave id empty to finish)")
    while True:
        emp_id = input("id:").strip()
        if not emp_id:
            break
        name = input("name:").strip()
        dob = input("DOB (DD/MM/YYYY):").strip()
        while not valid_date(dob):
            dob = input("Invalid.DOB(DD/MM/YYYY):").strip()
        email = input(" email_id: ").strip()
        rows.append([emp_id,name,dob,email])
        break

    if not rows:
        print("No data entered.")
        return
    print("\n"+ make_table(rows)+"\n")
    to = input("Send to (email):").strip()
    subject = input("Subject [Employee Details]:").strip() or "Employee Details"
    sent = send_employee_email(gmail,rows,to,subject)
    print(f"Email sent .Message id: {sent['id']}")

def get_body(message):
    parts = [message["payload"]]
    while parts:
        p = parts.pop(0)
        data = p.get("body",{}).get("data")
        if p.get("mimeType")== "text/plain" and data:
            return base64.urlsafe_b64decode(data).decode("utf-8",errors="replace").strip()
        parts += p.get("parts",[]) or []
    return message.get("snippet","")

def retrieve_unread(gmail,subject=search_subject,verbose=True):
    query = f'is:unread subject:"{subject}"'
    ids, token = [], None
    while True:
        resp = gmail.users().messages().list(
            userId="me", q=query,labelIds=["UNREAD"],pageToken=token).execute()
        ids += [m["id"] for m in resp.get("messages", [])]
        token = resp.get("nextPageToken")
        if not token:
            break
    mails = []
    for mid in ids:
        m = gmail.users().messages().get(userId="me",id=mid,format="full").execute()
        h = {x["name"].lower():x["value"] for x in m["payload"]["headers"]}
        if h.get("subject","").strip().lower()!=subject.strip().lower():
            continue
        mail = {"message_id": mid,
                "thread_id": m.get("threadId"),
                "rfc_message_id": h.get("message-id", ""),
                "from": h.get("from", ""),
                "subject": h.get("subject", ""),
                "date": h.get("date", ""),
                "body": get_body(m)}
        mails.append(mail)
        if verbose:
            print(f"[{len(mails)}] From: {mail['from']}")
            print(f"Subject: {mail['subject']}")
            print(f"Date: {mail['date']}")
            print("-" * 70)
            print(mail["body"])
            print()
    return mails

def reply_with_age(gmail, mail, verbose=True):
    sender = parseaddr(mail["from"])[1]
    rows = parse_table(mail["body"])
    if not sender or not rows:
        if verbose:
            print(f"Skipped mail {mail['message_id']}: no sender or no employee table found")
        return []
    rows = add_age(rows)
    subject = mail["subject"]
    if not subject.lower().startswith("re:"):
        subject = "Re: " + subject
    body = make_table(rows, headers_with_age)
    send_mail(gmail, sender, subject, body,
              thread_id=mail["thread_id"], in_reply_to=mail["rfc_message_id"])
    if verbose:
        print(f"Updated reply sent to {sender}")
    return rows_to_dicts(rows)

def mark_as_read(gmail, mails):
    gmail.users().messages().batchModify(
        userId="me",
        body={"ids": [m["message_id"] for m in mails],"removeLabelIds":["UNREAD"]}).execute()

def process_mails(gmail,verbose=True):
    mails = retrieve_unread(gmail,verbose=verbose)
    sent_data = []
    for mail in mails:
        sent_data += reply_with_age(gmail,mail,verbose=verbose)
    return mails,sent_data

def get_data(gmail=None,mark_read=False):
    gmail = gmail or get_gmail_service()
    mails, sent_data = process_mails(gmail,verbose=False)
    if mark_read and mails:
        mark_as_read(gmail,mails)
    return sent_data

def print_data(sent_data):
    print(sent_data)

def retrieve_flow(gmail):
    print(f"\nReading unread mails with subject:{search_subject}")
    mails, sent_data = process_mails(gmail)
    if not mails:
        print(f"No unread emails found with subject '{search_subject}'.")
        return
    print(f"Total unread found: {len(mails)}")

    print_data(sent_data)

    if input("\nMark these as read? (y/N): ").strip().lower() == "y":
        mark_as_read(gmail, mails)
        print("Marked as read")

def main():
    gmail = get_gmail_service()
    while True:
        print("1.send employee table email")
        print(f"2.retrieve unread'{search_subject}'emails(+ auto reply with age)")
        print("0.Exit")
        c = input("Choose:").strip()
        try:
            if c == "1":
                send_flow(gmail)
            elif c == "2":
                retrieve_flow(gmail)
            elif c == "0":
                break
            else:
                print("Invalid choice.")
        except Exception as e:
            print(f"Error: {e}")


main()

# data = get_data()      # returns the list of dictionaries(nothing print)
# print_data(data)     # prints it list of dictionary


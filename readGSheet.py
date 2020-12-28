import pandas as pd
from datetime import datetime
import numpy as np
from googleapiclient.discovery import build
import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def gsheet_api_check(SCOPES):
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'Extras/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def pull_sheet_data(SCOPES, SPREADSHEET_ID, RANGE_NAME):
    creds = gsheet_api_check(SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        rows = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                  range=RANGE_NAME).execute()
        data = rows.get('values')
        print("Imported GSHEET")
        return data

def read_sheet(sheet_ID, sheet_name):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    data = pull_sheet_data(SCOPES, sheet_ID, sheet_name)
    df = pd.DataFrame(data[1:], columns=data[0])
    return df

def get_sheets():
    sheet_ID = ''
    sheet_name = ''

    sheet_df = read_sheet(sheet_ID, sheet_name).sample(frac=1, weights='_Weight').reset_index(drop=True)
    rand_sheet_name = os.path.join('DataDump', 'randSheet_' + datetime.now().strftime('%H%M') + '.csv')
    sheet_df.to_csv(rand_sheet_name)
    sha, shb, shc = np.array_split(sheet_df, 3)
    return sheet_df, sha, shb, shc

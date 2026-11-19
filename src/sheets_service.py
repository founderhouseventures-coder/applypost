from oauth_credentials import get_user_credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets'
]


def get_sheets_service():
    from googleapiclient.discovery import build

    creds = get_user_credentials(SCOPES, 'token.json')
    return build('sheets', 'v4', credentials=creds)


def append_row(service, spreadsheet_id, sheet_name, row):
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{_quote_sheet_name(sheet_name)}!A:E",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]}
    ).execute()


def get_logged_message_ids(service, spreadsheet_id, sheet_name):
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{_quote_sheet_name(sheet_name)}!E:E",
    ).execute()
    return {row[0] for row in result.get("values", []) if row and row[0]}


def _quote_sheet_name(sheet_name):
    return "'" + sheet_name.replace("'", "''") + "'"

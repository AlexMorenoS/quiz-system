
import os

print(os.getcwd())

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    r"d:\Mardisresearch\OneDrive - mardisresearch.com\Documentos\99. Personal\ESPOL\quiz-system\sistemaquizzes-123456.json",
    scope
)

client = gspread.authorize(creds)

sheet = client.open("BancoPreguntas")

worksheet = sheet.worksheet("BancoPreguntas")

data = worksheet.get_all_records()

df = pd.DataFrame(data)

print(df.head())
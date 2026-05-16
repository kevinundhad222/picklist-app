import streamlit as st
import pdfplumber
import re
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(
    page_title="Picklist Automation",
    page_icon="📦"
)

st.title("📦 Picklist PDF To Google Sheet")

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "creds.json",
    scope
)

client = gspread.authorize(creds)

sheet = client.open("PICKLIST DATA").sheet1

uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"]
)

if uploaded_file:

    data = []

    with pdfplumber.open(uploaded_file) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if not text:
                continue

            text = text.replace(
                "SKU Size Qty Color Order No.",
                ""
            )

            lines = text.split("\n")

            i = 0

            while i < len(lines):

                line = lines[i].strip()

                if not line:
                    i += 1
                    continue

                skip_words = [
                    "SGST",
                    "CGST",
                    "IGST",
                    "Tax",
                    "Invoice",
                    "Total",
                    "Amount",
                    "HSN",
                    "Other",
                    "Rs.",
                    "Supplier",
                    "Address",
                    "Mobile",
                    "EAN"
                ]

                if any(word in line for word in skip_words):
                    i += 1
                    continue

                if (
                    "Free Size" not in line
                    and i + 1 < len(lines)
                    and "Free Size" in lines[i + 1]
                ):
                    line = line + " " + lines[i + 1].strip()
                    i += 1

                match1 = re.search(
                    r"^(.*?)\s+Free Size\s+(\d+)",
                    line
                )

                match2 = re.search(
                    r"^(\d+)\s+[\d.]+\s+(\d+)\s+",
                    line
                )

                if match1:

                    sku = match1.group(1).strip()

                    qty = int(match1.group(2))

                    data.append([sku, qty])

                elif match2:

                    sku = match2.group(1).strip()

                    qty = int(match2.group(2))

                    data.append([sku, qty])

                i += 1

    if data:

        sheet.clear()

        sheet.append_row(["SKU", "QTY"])

        sheet.append_rows(data)

        df = pd.DataFrame(data, columns=["SKU", "QTY"])

        st.success("✅ Google Sheet Updated!")

        st.dataframe(df)

    else:

        st.error("No SKU Data Found")

import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="DealMachine Lead Cleaner", layout="wide")
st.title("DealMachine Lead Cleaner")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

def detect_column(columns, keywords):
    for col in columns:
        for key in keywords:
            if key.lower() in col.lower():
                return col
    return None

def clean_address(addr):
    if pd.isna(addr):
        return addr
    addr = re.sub(r"[^\w\s#/-]", "", str(addr))  # remove symbols
    addr = addr.replace(" St ", " Street ")
    addr = addr.replace(" Ave ", " Avenue ")
    addr = addr.replace(" Rd ", " Road ")
    addr = addr.replace(" Dr ", " Drive ")
    addr = addr.replace(" N ", " North ")
    addr = addr.replace(" S ", " South ")
    addr = addr.replace(" E ", " East ")
    addr = addr.replace(" W ", " West ")
    return addr.strip()

if uploaded_file:
    df = pd.read_csv(uploaded_file, dtype=str)

    st.subheader("Preview of Uploaded Data")
    st.dataframe(df.head())

    columns = df.columns.tolist()
    st.write("Column Names in This File:", columns)

    address_col = detect_column(columns, ["address", "street", "property address", "prop address"])
    city_col = detect_column(columns, ["city", "property city"])
    state_col = detect_column(columns, ["state", "property state"])
    zip_col = detect_column(columns, ["zip", "zip code", "postal"])
    email_col = detect_column(columns, ["email", "e-mail"])
    first_name_col = detect_column(columns, ["first name", "owner first"])
    last_name_col = detect_column(columns, ["last name", "owner last"])

    st.subheader("Detected Columns")
    st.json({
        "Address": address_col,
        "City": city_col,
        "State": state_col,
        "Zip": zip_col,
        "Email": email_col,
        "First Name": first_name_col,
        "Last Name": last_name_col
    })

    if address_col:
        df[address_col] = df[address_col].apply(clean_address)

    df.drop_duplicates(subset=[address_col, city_col, state_col, zip_col], inplace=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Cleaned File", csv, "cleaned_leads.csv", "text/csv")

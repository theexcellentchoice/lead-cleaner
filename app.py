import streamlit as st
import pandas as pd
import re

st.title("Lead Cleaner for DealMachine & RESimpli")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

def detect_column(columns, keywords):
    for col in columns:
        for key in keywords:
            if key.lower() in col.lower():
                return col
    return None

def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r"[^\w\s\-#/]", "", text)  # remove special characters except dash, #, /
    text = re.sub(r"\s+", " ", text).strip()
    return text

if uploaded_file:
    df = pd.read_csv(uploaded_file, dtype=str)
    st.subheader("Preview of Uploaded Data")
    st.dataframe(df.head())

    columns = df.columns.tolist()

    st.subheader("Column Names in This File:")
    st.write(columns)

    # Auto detect columns
    address_col = detect_column(columns, ["address", "street", "property address", "prop address"])
    city_col = detect_column(columns, ["city", "property city"])
    state_col = detect_column(columns, ["state", "property state"])
    zip_col = detect_column(columns, ["zip", "zip code", "postal"])
    email_col = detect_column(columns, ["email", "e-mail", "email address"])
    first_name_col = detect_column(columns, ["first name", "owner first", "owner 1 first"])
    last_name_col = detect_column(columns, ["last name", "owner last", "owner 1 last"])
    full_name_col = detect_column(columns, ["full name", "contact name", "owner name"])

    detected = {
        "Address": address_col,
        "City": city_col,
        "State": state_col,
        "Zip": zip_col,
        "Email": email_col,
        "First Name": first_name_col,
        "Last Name": last_name_col,
    }

    st.subheader("Detected Columns")
    st.json(detected)

    # ---- NAME SPLITTING (NEW) ----
    if full_name_col and not first_name_col and not last_name_col:
        name_split = df[full_name_col].fillna("").str.strip().str.split(" ", n=1, expand=True)
        df["First Name"] = name_split[0]
        df["Last Name"] = name_split[1]
        first_name_col = "First Name"
        last_name_col = "Last Name"

    # ---- CLEAN ADDRESS FIELDS ----
    if address_col:
        df[address_col] = df[address_col].apply(clean_text)
    if city_col:
        df[city_col] = df[city_col].apply(clean_text)
    if state_col:
        df[state_col] = df[state_col].str.upper().str.strip()
    if zip_col:
        df[zip_col] = df[zip_col].str.extract(r"(\d{5})", expand=False)

    # ---- REMOVE BLANK ADDRESS ROWS ----
    if address_col:
        df = df[df[address_col].str.strip() != ""]

    # ---- DEDUPLICATE BY PROPERTY ADDRESS ----
    subset_cols = [col for col in [address_col, city_col, state_col, zip_col] if col]
    if subset_cols:
        df.drop_duplicates(subset=subset_cols, inplace=True)

    # ---- CLEAN EMAILS ----
    if email_col:
        df[email_col] = df[email_col].str.lower().str.strip()

    # ---- FINAL COLUMN STANDARDIZATION ----
    rename_map = {}
    if address_col: rename_map[address_col] = "Address Line 1"
    if city_col: rename_map[city_col] = "City"
    if state_col: rename_map[state_col] = "State"
    if zip_col: rename_map[zip_col] = "Zip Code"
    if email_col: rename_map[email_col] = "Email"
    if first_name_col: rename_map[first_name_col] = "First Name"
    if last_name_col: rename_map[last_name_col] = "Last Name"

    df.rename(columns=rename_map, inplace=True)

    st.subheader("Cleaned Data Preview")
    st.dataframe(df.head())

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Cleaned CSV", csv, "cleaned_leads.csv", "text/csv")

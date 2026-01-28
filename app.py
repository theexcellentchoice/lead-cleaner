import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Lead Cleaner", layout="wide")

st.title("Lead Cleaner")
st.write("Upload a lead list and clean it for RESimpli, DealMachine, or Email Outreach.")

uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r"[^\w\s\-#/]", "", text)
    return text.strip()

def normalize_email(email):
    if pd.isna(email):
        return ""
    return str(email).strip().lower()

def detect_column(columns, keywords):
    for col in columns:
        for key in keywords:
            if key in col.lower():
                return col
    return None

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("Preview of Uploaded Data")
    st.dataframe(df.head())

    columns = df.columns.tolist()

address_col = detect_column(columns, ["address", "street", "property address", "prop address"])
city_col = detect_column(columns, ["city", "property city"])
state_col = detect_column(columns, ["state", "property state"])
zip_col = detect_column(columns, ["zip", "zip code", "postal"])
email_col = detect_column(columns, ["email", "e-mail", "email address"])
first_name_col = detect_column(columns, ["first name", "owner first", "owner 1 first"])
last_name_col = detect_column(columns, ["last name", "owner last", "owner 1 last"])

    st.subheader("Detected Columns")
    st.write({
        "Address": address_col,
        "City": city_col,
        "State": state_col,
        "Zip": zip_col,
        "Email": email_col,
        "First Name": first_name_col,
        "Last Name": last_name_col
    })

    if st.button("Clean Data"):
        clean_df = pd.DataFrame()

        if address_col:
            clean_df["Address Line 1"] = df[address_col].apply(clean_text)
        if city_col:
            clean_df["City"] = df[city_col].apply(clean_text)
        if state_col:
            clean_df["State"] = df[state_col].apply(clean_text)
        if zip_col:
            clean_df["Zip Code"] = df[zip_col].astype(str).str.zfill(5)
        if email_col:
            clean_df["Email"] = df[email_col].apply(normalize_email)
        if first_name_col:
            clean_df["First Name"] = df[first_name_col].apply(clean_text)
        if last_name_col:
            clean_df["Last Name"] = df[last_name_col].apply(clean_text)

        clean_df = clean_df.drop_duplicates()
        clean_df = clean_df.replace("", pd.NA).dropna(how="all")

        st.success("Cleaning complete!")

        st.download_button(
            label="Download Cleaned CSV",
            data=clean_df.to_csv(index=False),
            file_name="cleaned_leads.csv",
            mime="text/csv"
        )


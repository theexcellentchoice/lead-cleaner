import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Lead Cleaner Pro", layout="wide")

st.title("🧼 Lead Cleaner Pro")
st.write("Upload a CSV exported from DealMachine, REsimpli, or your data source.")

# ---------- Helpers ----------

def clean_text(val):
    if pd.isna(val):
        return ""
    val = str(val)
    val = val.replace("\u00A0", " ")  # non-breaking space
    val = re.sub(r'[\x00-\x1F]+', '', val)  # non-printable chars
    val = val.strip()
    return val

def clean_email(email):
    email = clean_text(email).lower()
    email = re.sub(r'\s+', '', email)
    return email

def clean_name(name):
    name = clean_text(name)
    return name.title()

def normalize_address(addr):
    addr = clean_text(addr)
    addr = re.sub(r'\s+', ' ', addr)
    return addr.title()

def detect_column(columns, keywords):
    for col in columns:
        for key in keywords:
            if key in col.lower():
                return col
    return None

def split_unit(address):
    patterns = [
        r'(.*)\s+#\s*(\w+)',
        r'(.*)\s+apt\.?\s*(\w+)',
        r'(.*)\s+unit\s*(\w+)',
        r'(.*)\s+suite\s*(\w+)',
        r'(.*)\s+#(\w+)',
    ]
    for pattern in patterns:
        match = re.match(pattern, address, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
    return address, ""

# ---------- File Upload ----------

file = st.file_uploader("Upload CSV File", type=["csv"])

if file:
    df = pd.read_csv(file, dtype=str)
    df = df.applymap(clean_text)

    st.subheader("Preview of Uploaded Data")
    st.dataframe(df.head())

    columns = df.columns.tolist()
    st.write("### Column Names in This File:")
    st.write(columns)

    # Auto detect columns
    address_col = detect_column(columns, ["address", "property address", "street"])
    city_col = detect_column(columns, ["city"])
    state_col = detect_column(columns, ["state"])
    zip_col = detect_column(columns, ["zip"])
    email_col = detect_column(columns, ["email"])
    first_name_col = detect_column(columns, ["first"])
    last_name_col = detect_column(columns, ["last"])

    detected = {
        "Address": address_col,
        "City": city_col,
        "State": state_col,
        "Zip": zip_col,
        "Email": email_col,
        "First Name": first_name_col,
        "Last Name": last_name_col
    }

    st.subheader("Detected Columns")
    st.json(detected)

    # ---------- Cleaning ----------
    if email_col:
        df[email_col] = df[email_col].apply(clean_email)

    if first_name_col:
        df[first_name_col] = df[first_name_col].apply(clean_name)

    if last_name_col:
        df[last_name_col] = df[last_name_col].apply(clean_name)

    if address_col:
        df[address_col] = df[address_col].apply(normalize_address)

    # Remove duplicates by full property
    if address_col and city_col and state_col and zip_col:
        df.drop_duplicates(subset=[address_col, city_col, state_col, zip_col], inplace=True)

    # ---------- Standard Output ----------
    st.subheader("📦 Standard Cleaned File (REsimpli / Instantly)")
    csv_standard = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Standard Cleaned CSV", csv_standard, "cleaned_standard.csv", "text/csv")

    # ---------- DealMachine Mode ----------
    st.subheader("🟦 DealMachine Mode File")
    if address_col:
        dm_df = df.copy()
        dm_df["Address Line 1"] = ""
        dm_df["Address Line 2"] = ""

        for i, addr in dm_df[address_col].items():
            line1, unit = split_unit(addr)
            dm_df.at[i, "Address Line 1"] = line1
            dm_df.at[i, "Address Line 2"] = unit

        csv_dm = dm_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download DealMachine CSV", csv_dm, "cleaned_dealmachine.csv", "text/csv")

    st.success("Cleaning complete! Download the file version you need.")

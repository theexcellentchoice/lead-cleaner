import streamlit as st
import pandas as pd
import re

st.title("Lead List Cleaner for DealMachine")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

# ---------- ADDRESS HELPERS ----------

street_replacements = {
    " St ": " Street ",
    " Ave ": " Avenue ",
    " Rd ": " Road ",
    " Dr ": " Drive ",
    " Ln ": " Lane ",
    " Blvd ": " Boulevard ",
    " Ct ": " Court ",
    " Pl ": " Place ",
    " Pkwy ": " Parkway ",
    " Cir ": " Circle ",
    " Ter ": " Terrace ",
    " Hwy ": " Highway "
}

direction_replacements = {
    " N ": " North ",
    " S ": " South ",
    " E ": " East ",
    " W ": " West ",
    " NE ": " Northeast ",
    " NW ": " Northwest ",
    " SE ": " Southeast ",
    " SW ": " Southwest "
}

def clean_address_text(addr):
    if not isinstance(addr, str):
        return ""
    addr = " " + addr.strip() + " "

    for k, v in street_replacements.items():
        addr = addr.replace(k, v)

    for k, v in direction_replacements.items():
        addr = addr.replace(k, v)

    addr = re.sub(r"\s+", " ", addr)
    return addr.strip().title()

def split_unit(address):
    if not isinstance(address, str):
        return address, ""

    addr = address.strip()

    patterns = [
        r'(.*)\s+(Apt\.?|Apartment)\s*#?\s*([\w\-]+)$',
        r'(.*)\s+(Unit)\s*#?\s*([\w\-]+)$',
        r'(.*)\s+#\s*([\w\-]+)$',
        r'(.*)\s+(Room)\s*([\w\-]+)$',
        r'(.*)\s+(Suite|Ste\.?)\s*([\w\-]+)$',
        r'(.*)\s+(Lower Front|Upper|Lower|Front|Rear)$'
    ]

    for pattern in patterns:
        match = re.match(pattern, addr, re.IGNORECASE)
        if match:
            base = match.group(1).strip()
            unit_parts = match.groups()[1:]
            unit = " ".join([p for p in unit_parts if p])
            return base, unit.title()

    return addr, ""

# ---------- COLUMN DETECTION ----------

def detect_column(columns, keywords):
    for col in columns:
        col_lower = col.lower()
        for key in keywords:
            if key in col_lower:
                return col
    return None

# ---------- MAIN PROCESS ----------

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("Column Names in This File")
    st.write(df.columns.tolist())

    columns = df.columns.tolist()

    address_col = detect_column(columns, ["address", "street", "property address"])
    city_col = detect_column(columns, ["city"])
    state_col = detect_column(columns, ["state"])
    zip_col = detect_column(columns, ["zip"])
    email_col = detect_column(columns, ["email"])
    first_name_col = detect_column(columns, ["first name"])
    last_name_col = detect_column(columns, ["last name"])

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

    # Clean address and split unit
    if address_col:
        df[['Address Line 1', 'Address Line 2']] = df[address_col].apply(
            lambda x: pd.Series(split_unit(clean_address_text(x)))
        )
    else:
        df['Address Line 1'] = ""
        df['Address Line 2'] = ""

    # Clean city/state
    if city_col:
        df['City'] = df[city_col].astype(str).str.strip().str.title()
    else:
        df['City'] = ""

    if state_col:
        df['State'] = df[state_col].astype(str).str.strip().str.upper()
    else:
        df['State'] = ""

    if zip_col:
        df['Zip Code'] = df[zip_col].astype(str).str.strip().str.zfill(5)
    else:
        df['Zip Code'] = ""

    # Remove duplicates
    df.drop_duplicates(subset=['Address Line 1', 'City', 'State', 'Zip Code'], inplace=True)

    st.subheader("Preview of Cleaned Data")
    st.dataframe(df.head())

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Cleaned CSV", csv, "cleaned_leads.csv", "text/csv")

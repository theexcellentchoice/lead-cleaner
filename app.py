import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Lead Cleaner", layout="wide")
st.title("Lead List Cleaning Engine")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

# ---------- Helper Functions ----------

def detect_column(columns, keywords):
    for col in columns:
        for key in keywords:
            if key.lower() in col.lower():
                return col
    return None

def clean_text(val):
    if pd.isna(val):
        return ""
    val = str(val)
    val = re.sub(r'\u00A0', ' ', val)
    val = re.sub(r'[\x00-\x1F]', '', val)
    return re.sub(r'\s+', ' ', val).strip()

def expand_abbreviations(addr):
    replacements = {
        r'\bSt\b': 'Street',
        r'\bAve\b': 'Avenue',
        r'\bRd\b': 'Road',
        r'\bBlvd\b': 'Boulevard',
        r'\bDr\b': 'Drive',
        r'\bLn\b': 'Lane',
        r'\bCt\b': 'Court',
        r'\bPl\b': 'Place',
        r'\bTer\b': 'Terrace',
        r'\bCir\b': 'Circle',
        r'\bPkwy\b': 'Parkway',
        r'\bHwy\b': 'Highway'
    }
    for pattern, replacement in replacements.items():
        addr = re.sub(pattern, replacement, addr, flags=re.IGNORECASE)
    return addr

def expand_directions(addr):
    directions = {
        r'\bN\b': 'North',
        r'\bS\b': 'South',
        r'\bE\b': 'East',
        r'\bW\b': 'West',
        r'\bNE\b': 'Northeast',
        r'\bNW\b': 'Northwest',
        r'\bSE\b': 'Southeast',
        r'\bSW\b': 'Southwest'
    }
    for pattern, replacement in directions.items():
        addr = re.sub(pattern, replacement, addr)
    return addr

def fix_ordinals(addr):
    return re.sub(r'\b(\d+)(ST|ND|RD|TH)\b', lambda m: m.group(1) + m.group(2).lower(), addr)

def separate_unit(addr):
    unit_patterns = [
        r'(.*?)(\s+#\s*\w+)$',
        r'(.*?)(\s+APT\s*\w+)$',
        r'(.*?)(\s+UNIT\s*\w+)$',
        r'(.*?)(\s+SUITE\s*\w+)$',
        r'(.*?)(\s+LOT\s*\w+)$'
    ]
    for pattern in unit_patterns:
        match = re.search(pattern, addr, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
    return addr, ""

def clean_address(addr):
    addr = clean_text(addr)
    addr = expand_abbreviations(addr)
    addr = expand_directions(addr)
    addr = fix_ordinals(addr)
    addr = re.sub(r'(\d+)([A-Za-z])\b', r'\1 \2', addr)
    addr = re.sub(r'[^\w\s#-]', '', addr)
    addr = re.sub(r'\s+', ' ', addr).strip().title()
    return addr

# ---------- Processing ----------

if uploaded_file:
    df = pd.read_csv(uploaded_file, dtype=str)
    df = df.applymap(clean_text)

    columns = df.columns.tolist()

    st.subheader("Column Names in This File")
    st.write(columns)

    address_col = detect_column(columns, ["address", "street", "property address"])
    city_col = detect_column(columns, ["city"])
    state_col = detect_column(columns, ["state"])
    zip_col = detect_column(columns, ["zip"])
    email_col = detect_column(columns, ["email"])
    first_name_col = detect_column(columns, ["first"])
    last_name_col = detect_column(columns, ["last"])

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

    if address_col and city_col and state_col and zip_col:

        df[address_col] = df[address_col].apply(clean_address)
        df["Address Line 1"], df["Address Line 2"] = zip(*df[address_col].apply(separate_unit))

        df["City"] = df[city_col].str.title()
        df["State"] = df[state_col].str.upper()
        df["Zip Code"] = df[zip_col].str.extract(r'(\d{5})', expand=False).fillna("")

        if email_col:
            df["Email"] = df[email_col].str.lower().str.strip()
            df = df[df["Email"].str.contains("@", na=False)]

        if first_name_col:
            df["First Name"] = df[first_name_col].str.title()
        if last_name_col:
            df["Last Name"] = df[last_name_col].str.title()

        df.drop_duplicates(subset=["Address Line 1", "City", "State", "Zip Code"], inplace=True)
        df = df[df["Address Line 1"] != ""]

        st.success(f"Cleaning complete! {len(df)} leads ready.")

        output_cols = [
            "First Name", "Last Name", "Email",
            "Address Line 1", "Address Line 2",
            "City", "State", "Zip Code"
        ]
        final_df = df[[col for col in output_cols if col in df.columns]]

        st.download_button(
            "Download Cleaned CSV",
            final_df.to_csv(index=False),
            "cleaned_leads.csv",
            "text/csv"
        )

    else:
        st.error("Required address columns not detected.")

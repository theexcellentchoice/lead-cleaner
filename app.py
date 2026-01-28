import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Lead Cleaner Pro", layout="wide")
st.title("📬 Lead Cleaner Pro")
st.write("Cleans and standardizes lead data for DealMachine, REsimpli, and email marketing.")

# =============================
# COLUMN DETECTION
# =============================
def detect_column(columns, keywords):
    for col in columns:
        for keyword in keywords:
            if keyword.lower() in col.lower():
                return col
    return None

# =============================
# BASIC TEXT CLEANING
# =============================
def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = text.replace('\u00A0', ' ')  # non-breaking spaces
    text = re.sub(r'[\x00-\x1F]+', '', text)  # hidden characters
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# =============================
# ADDRESS CLEANING
# =============================
def separate_unit(addr):
    unit_pattern = r'(?:#|Apt|Unit|Suite|Ste|Lot|Fl|Floor|Bldg|Building)\s*[\w-]+'
    match = re.search(unit_pattern, addr, re.IGNORECASE)
    if match:
        unit = match.group()
        addr = addr.replace(unit, '').strip()
        return addr, unit
    return addr, ""

def to_usps_abbreviations(addr):
    replacements = {
        r'\bStreet\b': 'St', r'\bAvenue\b': 'Ave', r'\bRoad\b': 'Rd',
        r'\bBoulevard\b': 'Blvd', r'\bDrive\b': 'Dr', r'\bLane\b': 'Ln',
        r'\bCourt\b': 'Ct', r'\bPlace\b': 'Pl', r'\bTerrace\b': 'Ter',
        r'\bCircle\b': 'Cir', r'\bParkway\b': 'Pkwy', r'\bHighway\b': 'Hwy'
    }
    for pattern, replacement in replacements.items():
        addr = re.sub(pattern, replacement, addr, flags=re.IGNORECASE)
    return addr

def to_usps_directions(addr):
    directions = {
        r'\bNorth\b': 'N', r'\bSouth\b': 'S', r'\bEast\b': 'E', r'\bWest\b': 'W',
        r'\bNortheast\b': 'NE', r'\bNorthwest\b': 'NW',
        r'\bSoutheast\b': 'SE', r'\bSouthwest\b': 'SW'
    }
    for pattern, replacement in directions.items():
        addr = re.sub(pattern, replacement, addr, flags=re.IGNORECASE)
    return addr

def fix_ordinals(addr):
    return re.sub(r'\b(\d+)(ST|ND|RD|TH)\b', lambda m: m.group(1) + m.group(2).lower(), addr)

def clean_address(addr):
    addr = clean_text(addr)
    addr1, addr2 = separate_unit(addr)
    addr1 = to_usps_directions(addr1)
    addr1 = to_usps_abbreviations(addr1)
    addr1 = fix_ordinals(addr1)
    addr1 = re.sub(r'[^\w\s#-]', '', addr1)
    addr1 = re.sub(r'\s+', ' ', addr1).strip()
    return addr1.title(), addr2.title()

# =============================
# EMAIL + PHONE CLEANING
# =============================
def clean_email(email):
    email = clean_text(email).lower()
    email = re.sub(r'\s+', '', email)
    return email

def clean_phone(phone):
    phone = re.sub(r'\D', '', str(phone))
    return phone if len(phone) == 10 else ""

# =============================
# FILE UPLOAD
# =============================
uploaded_file = st.file_uploader("Upload CSV or Excel File", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("Preview of Uploaded Data")
    st.dataframe(df.head())

    columns = df.columns.tolist()

    # Auto detect columns
    address_col = detect_column(columns, ["address", "property address", "street"])
    city_col = detect_column(columns, ["city"])
    state_col = detect_column(columns, ["state"])
    zip_col = detect_column(columns, ["zip", "postal"])
    email_col = detect_column(columns, ["email"])
    phone_col = detect_column(columns, ["phone"])
    first_name_col = detect_column(columns, ["first name"])
    last_name_col = detect_column(columns, ["last name"])

    st.subheader("Detected Columns")
    st.json({
        "Address": address_col,
        "City": city_col,
        "State": state_col,
        "Zip": zip_col,
        "Email": email_col,
        "Phone": phone_col,
        "First Name": first_name_col,
        "Last Name": last_name_col
    })

    if st.button("🚀 Run Full Lead Cleaning"):
        # Clean basic text everywhere
        df = df.applymap(clean_text)

        # Address cleaning
        if address_col:
            df["Address Line 1"], df["Address Line 2"] = zip(*df[address_col].apply(clean_address))

        # Email + phone cleaning
        if email_col:
            df[email_col] = df[email_col].apply(clean_email)
        if phone_col:
            df[phone_col] = df[phone_col].apply(clean_phone)

        # Safe dedupe
        dedupe_cols = [col for col in [address_col, city_col, state_col, zip_col] if col]
        if dedupe_cols:
            df.drop_duplicates(subset=dedupe_cols, inplace=True)

        st.success("✅ Cleaning complete!")

        output = BytesIO()
        df.to_csv(output, index=False)
        st.download_button("📥 Download Cleaned File", data=output.getvalue(), file_name="cleaned_leads.csv", mime="text/csv")

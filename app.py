import streamlit as st
import pandas as pd
import pytesseract
import cv2
import numpy as np
from PIL import Image
from pypdf import PdfReader
import re
import io
import os


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Automated Document OCR",
    page_icon="📄",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title("📄 Automated Document OCR & Data Extractor")

st.write(
    "Upload an image or PDF document to extract text and important information automatically."
)


# ============================================================
# FUNCTIONS
# ============================================================

def preprocess_image(image):
    """
    Improve image quality before OCR.
    """

    # Convert PIL image to OpenCV format
    image = np.array(image)

    # Convert RGB to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Remove noise
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # Improve text visibility
    processed = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    return processed


def extract_text_from_image(image):
    """
    Extract text from image using Tesseract OCR.
    """

    processed_image = preprocess_image(image)

    text = pytesseract.image_to_string(
        processed_image,
        config="--psm 6"
    )

    return text


def extract_text_from_pdf(file):
    """
    Extract text from PDF.
    """

    reader = PdfReader(file)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def find_email(text):
    """
    Find email address.
    """

    pattern = r'[\w\.-]+@[\w\.-]+\.\w+'

    match = re.search(pattern, text)

    if match:
        return match.group()

    return "Not found"


def find_phone(text):
    """
    Find Indian phone number.
    """

    pattern = r'(?:\+91[\s-]?)?[6-9]\d{9}'

    match = re.search(pattern, text)

    if match:
        return match.group()

    return "Not found"


def find_date(text):
    """
    Find common date formats.
    """

    patterns = [
        r'\b\d{2}/\d{2}/\d{4}\b',
        r'\b\d{2}-\d{2}-\d{4}\b',
        r'\b\d{4}-\d{2}-\d{2}\b'
    ]

    for pattern in patterns:

        match = re.search(pattern, text)

        if match:
            return match.group()

    return "Not found"


def find_name(text):
    """
    Try to find a name from lines containing 'Name'.
    """

    lines = text.splitlines()

    for line in lines:

        if "name" in line.lower():

            parts = re.split(
                r'[:\-]',
                line,
                maxsplit=1
            )

            if len(parts) == 2:

                value = parts[1].strip()

                if value:
                    return value

    return "Not found"


def find_document_number(text):
    """
    Try to find a document number.
    """

    keywords = [
        "document number",
        "document no",
        "document id",
        "id number",
        "application number",
        "application no",
        "certificate number",
        "certificate no"
    ]

    lines = text.splitlines()

    for line in lines:

        lower_line = line.lower()

        for keyword in keywords:

            if keyword in lower_line:

                parts = re.split(
                    r'[:\-]',
                    line,
                    maxsplit=1
                )

                if len(parts) == 2:

                    value = parts[1].strip()

                    if value:
                        return value

    return "Not found"


def extract_data(text):
    """
    Extract important fields from OCR text.
    """

    data = {
        "Name": find_name(text),
        "Email": find_email(text),
        "Phone": find_phone(text),
        "Date": find_date(text),
        "Document Number": find_document_number(text)
    }

    return data


# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "Upload your document",
    type=[
        "jpg",
        "jpeg",
        "png",
        "pdf"
    ]
)


# ============================================================
# PROCESS DOCUMENT
# ============================================================

if uploaded_file is not None:

    st.success(
        f"Uploaded: {uploaded_file.name}"
    )

    file_extension = os.path.splitext(
        uploaded_file.name
    )[1].lower()


    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    if file_extension in [
        ".jpg",
        ".jpeg",
        ".png"
    ]:

        image = Image.open(uploaded_file)

        st.subheader("📷 Uploaded Document")

        st.image(
            image,
            width=500
        )

        if st.button("🔍 Extract Data"):

            with st.spinner("Reading document..."):

                try:

                    text = extract_text_from_image(
                        image
                    )

                    data = extract_data(
                        text
                    )

                    st.session_state["text"] = text
                    st.session_state["data"] = data

                    st.success(
                        "Document processed successfully!"
                    )

                except Exception as e:

                    st.error(
                        f"Error: {e}"
                    )


    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    elif file_extension == ".pdf":

        if st.button("🔍 Extract Data"):

            with st.spinner("Reading PDF..."):

                try:

                    text = extract_text_from_pdf(
                        uploaded_file
                    )

                    data = extract_data(
                        text
                    )

                    st.session_state["text"] = text
                    st.session_state["data"] = data

                    st.success(
                        "PDF processed successfully!"
                    )

                except Exception as e:

                    st.error(
                        f"Error: {e}"
                    )


# ============================================================
# SHOW RESULTS
# ============================================================

if "data" in st.session_state:

    st.divider()

    st.header("📊 Extracted Information")

    data = st.session_state["data"]

    # Convert dictionary to DataFrame
    df = pd.DataFrame(
        list(data.items()),
        columns=[
            "Field",
            "Value"
        ]
    )

    st.table(df)


    # ========================================================
    # EXTRACTED TEXT
    # ========================================================

    st.subheader("📝 Extracted Text")

    st.text_area(
        "OCR Text",
        st.session_state["text"],
        height=300
    )


    # ========================================================
    # CSV DOWNLOAD
    # ========================================================

    csv = df.to_csv(
        index=False
    )

    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name="extracted_data.csv",
        mime="text/csv"
    )


    # ========================================================
    # JSON DOWNLOAD
    # ========================================================

    import json

    json_data = json.dumps(
        data,
        indent=4
    )

    st.download_button(
        label="⬇️ Download JSON",
        data=json_data,
        file_name="extracted_data.json",
        mime="application/json"
    )
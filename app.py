
# Giordano WhatsApp-Style Catalogue Generator (Local Streamlit App)

import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
from fpdf import FPDF
import zipfile

# Setup directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output")
CARD_DIR = OUTPUT_DIR / "cards"
for d in [UPLOAD_DIR, OUTPUT_DIR, CARD_DIR]:
    d.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Giordano Catalogue Generator", layout="wide")
st.title("🛍️ Giordano WhatsApp-Style Catalogue Generator")

# Upload logo
logo_file = st.file_uploader("Upload Brand Logo", type=["png", "jpg"])

# Upload Excel file
excel_file = st.file_uploader("Upload Excel/CSV file with product data", type=["xlsx", "csv"])

# Upload product images
images_zip = st.file_uploader("Upload ZIP of Product Images (named by Model No.)", type="zip")

# Layout options
cards_per_row = st.selectbox("Cards per row", [2, 3])

if st.button("Generate Catalogue") and excel_file and images_zip:
    with st.spinner("Processing..."):
        # Extract uploaded ZIP of images
        with zipfile.ZipFile(images_zip, 'r') as zip_ref:
            zip_ref.extractall(UPLOAD_DIR / "images")

        # Load product data
        if excel_file.name.endswith(".csv"):
            df = pd.read_csv(excel_file)
        else:
            df = pd.read_excel(excel_file, header=None, skiprows=6)
            df.columns = ["S.No", "Model", "EAN", "MRP", "Gender", "Discount", "CSP", "Inventory", "Remarks"]

        # Load logo
        logo = Image.open(logo_file).convert("RGBA") if logo_file else None

        card_paths = []

        # Font setup
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()

        for idx, row in df.iterrows():
            model = str(row["Model"]).strip()
            image_path = UPLOAD_DIR / "images" / f"{model}.jpg"
            if not image_path.exists():
                continue

            # Open product image
            base = Image.open(image_path).convert("RGB")
            base = base.resize((500, 500))

            draw = ImageDraw.Draw(base)
            draw.rectangle([(0, 420), (500, 500)], fill="white")
            draw.text((10, 430), f"Model: {model}", fill="black", font=font)
            draw.text((10, 455), f"MRP: ₹{int(row['MRP'])}  Offer: ₹{int(row['CSP'])}", fill="black", font=font)
            draw.text((10, 480), f"Stock: {row['Inventory']}  {row['Remarks']}", fill="black", font=font)

            out_path = CARD_DIR / f"{model}.jpg"
            base.save(out_path)
            card_paths.append(out_path)

        # Save logo to file
        if logo:
            logo_path = OUTPUT_DIR / "temp_logo.png"
            logo.save(logo_path)

        # PDF creation
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        cards_per_page = cards_per_row * 2  # Assuming 2 rows

        for i in range(0, len(card_paths), cards_per_page):
            pdf.add_page()
            # Add logo once on first page
            if i == 0 and logo:
                pdf.image(str(logo_path), x=75, y=5, w=60)

            chunk = card_paths[i:i+cards_per_page]
            x_offsets = {2: [10, 110], 3: [10, 75, 140]}[cards_per_row]
            y_positions = [30, 155]

            for idx2, card in enumerate(chunk):
                col = idx2 % cards_per_row
                row = idx2 // cards_per_row
                if row < 2:
                    pdf.image(str(card), x=x_offsets[col], y=y_positions[row], w=65)

        pdf_output_path = OUTPUT_DIR / "Giordano_Catalogue.pdf"
        pdf.output(str(pdf_output_path))

        st.success("Catalogue created successfully!")
        st.download_button("📄 Download Catalogue PDF", data=pdf_output_path.read_bytes(), file_name="Giordano_Catalogue.pdf")

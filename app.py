# Git Setup Commands

git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/abdo11omar/product.git
git push -u origin main --force

# Web App Code (Streamlit - app.py)

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import csv
import os

# Caching for faster development
@st.cache_data

def search_and_scrape(model, brand):
    search_url = ""
    if brand.lower() == "gorenje":
        search_url = f"https://www.gorenje.com/search?q={model}"
    elif brand.lower() == "elba":
        search_url = f"https://www.elba-cookers.com/search?q={model}"
    else:
        return [], ""

    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    links = soup.find_all("a", href=True)
    product_page = None
    for link in links:
        if model.lower() in link["href"].lower():
            product_page = link["href"]
            break

    if not product_page:
        return [], ""

    if not product_page.startswith("http"):
        if brand.lower() == "gorenje":
            product_page = "https://www.gorenje.com" + product_page
        elif brand.lower() == "elba":
            product_page = "https://www.elba-cookers.com" + product_page

    prod_resp = requests.get(product_page, headers=headers)
    prod_soup = BeautifulSoup(prod_resp.text, "html.parser")

    imgs = prod_soup.find_all("img")
    img_urls = [img["src"] for img in imgs if "src" in img.attrs and any(x in img["src"] for x in [".jpg", ".png"])]
    img_urls = list(set([i if i.startswith("http") else f"https:{i}" for i in img_urls]))

    desc_tag = prod_soup.find("meta", {"name": "description"})
    desc = desc_tag["content"] if desc_tag and "content" in desc_tag.attrs else ""

    return img_urls, desc

# Streamlit UI
st.title("🛒 Shopify Product Scraper for Gorenje & Elba")
st.markdown("""
Upload your Excel file containing product models. This tool will:

1. 🔍 Search the official sites of Gorenje and Elba.
2. 📸 Fetch all product images.
3. 📝 Extract product description (if missing).
4. 📦 Export a Shopify-ready CSV file.
""")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df["Images"] = ""
    df["Description"] = ""

    for i, row in df.iterrows():
        model = str(row["Model"]) if "Model" in row else str(row[0])
        brand = str(row["Brand"]) if "Brand" in row else str(row[1])
        st.write(f"🔎 Scraping for {model} ({brand})")
        images, desc = search_and_scrape(model, brand)
        df.at[i, "Images"] = ", ".join(images)
        df.at[i, "Description"] = desc

    st.success("✅ Scraping Done!")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Shopify CSV", csv, file_name="shopify_products.csv", mime="text/csv")

# Requirements.txt
# streamlit
# pandas
# openpyxl
# beautifulsoup4
# requests

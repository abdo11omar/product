import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="Shopify Product Scraper", layout="wide")
st.title("📦 Shopify Product Scraper for Gorenje & Elba")

st.markdown("""
Upload your Excel file containing product models. This tool will:
1. Search the official sites of Gorenje and Elba.
2. Fetch all product images.
3. Extract product description (if missing).
4. Export a Shopify-ready CSV file.
""")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

@st.cache_data
@st.cache_data
def search_and_scrape(model, brand):
    if not isinstance(brand, str) or not isinstance(model, str):
        return [], ""

    search_url = ""
    if brand.lower() == "gorenje":
        search_url = f"https://www.gorenje.com/search?q={model}"
    elif brand.lower() == "elba":
        search_url = f"https://www.elba-cookers.com/en/search-results?searchword={model}"
    else:
        return [], ""

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    product_page = soup.find('a', href=True)
    if not product_page:
        return [], ""

    product_url = product_page['href'] if product_page['href'].startswith('http') else f"https://{brand.lower()}.com{product_page['href']}"
    prod_resp = requests.get(product_url, headers=headers)
    prod_soup = BeautifulSoup(prod_resp.text, 'html.parser')

    images = [img['src'] for img in prod_soup.find_all('img', src=True) if model.lower() in img['src'].lower()]
    description_tag = prod_soup.find(['p', 'div'], text=True)
    description = description_tag.get_text(strip=True) if description_tag else ""

    return images, description

    search_url = ""
    if brand.lower() == "gorenje":
        search_url = f"https://www.gorenje.com/search?q={model}"
    elif brand.lower() == "elba":
        search_url = f"https://www.elba-cookers.com/en/search-results?searchword={model}"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    product_page = soup.find('a', href=True)
    if not product_page:
        return [], ""

    product_url = product_page['href'] if product_page['href'].startswith('http') else f"https://{brand.lower()}.com{product_page['href']}"
    prod_resp = requests.get(product_url, headers=headers)
    prod_soup = BeautifulSoup(prod_resp.text, 'html.parser')

    images = [img['src'] for img in prod_soup.find_all('img', src=True) if model.lower() in img['src'].lower()]
    description_tag = prod_soup.find(['p', 'div'], text=True)
    description = description_tag.get_text(strip=True) if description_tag else ""

    return images, description

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if 'Model' not in df.columns or 'Brand' not in df.columns:
        st.error("Excel file must contain at least 'Brand' and 'Model' columns.")
    else:
        df_result = df.copy()
        df_result['Image Src'] = ""
        df_result['Body (HTML)'] = df_result.get('USP Arabic', "")

        with st.spinner("Scraping product data..."):
            for i, row in df.iterrows():
                brand = row['Brand']
                model = row['Model']
                images, desc = search_and_scrape(model, brand)
                
                df_result.at[i, 'Image Src'] = ",".join(images)
                if not df_result.at[i, 'Body (HTML)']:
                    df_result.at[i, 'Body (HTML)'] = desc
                time.sleep(1.5)

        st.success("Scraping completed!")
        st.dataframe(df_result.head())

        csv = df_result.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Download Shopify CSV", data=csv, file_name="shopify_products.csv", mime='text/csv')

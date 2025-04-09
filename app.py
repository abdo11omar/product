import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

@st.cache_data
def search_and_scrape(model, brand):
    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = ""

    if brand.lower() == "gorenje":
        search_url = f"https://www.eg.gorenje.com/en/search?q={model}"
        base_url = "https://www.gorenje.com"
    elif brand.lower() == "elba":
        search_url = f"https://www.elba-cookers.com/search?q={model}"
        base_url = "https://www.elba-cookers.com"
    else:
        return [], ""

    resp = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    product_page = None
    for a in soup.find_all("a", href=True):
        if model.lower() in a["href"].lower():
            product_page = a["href"]
            break

    if not product_page:
        return [], ""

    if not product_page.startswith("http"):
        product_page = base_url + product_page

    prod_resp = requests.get(product_page, headers=headers)
    prod_soup = BeautifulSoup(prod_resp.text, "html.parser")

    # استخراج الصور من <img> tags
    imgs = prod_soup.find_all("img")
    img_urls = []
    for img in imgs:
        src = img.get("src") or img.get("data-src")
        if src and any(ext in src for ext in [".jpg", ".png", ".jpeg"]):
            full_url = src if src.startswith("http") else f"https:{src}"
            img_urls.append(full_url)

    img_urls = list(set(img_urls))  # إزالة التكرارات

    # استخراج وصف المنتج من meta أو paragraph
    desc = ""
    meta_desc = prod_soup.find("meta", {"name": "description"})
    if meta_desc and meta_desc.get("content"):
        desc = meta_desc["content"]
    else:
        p = prod_soup.find("p")
        desc = p.text.strip() if p else ""

    return img_urls, desc

# واجهة Streamlit
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
        model = str(row.get("Model", row[0]))
        brand = str(row.get("Brand", row[1]))

        st.info(f"🔎 Scraping for {model} ({brand}) ...")

        images, desc = search_and_scrape(model, brand)

        df.at[i, "Images"] = ", ".join(images)
        df.at[i, "Description"] = desc

        # عرض الصور داخل Streamlit
        if images:
            st.image(images[0], width=300, caption=f"{model}")
        else:
            st.warning("❌ No images found.")

    st.success("✅ Scraping Done!")

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Shopify CSV", csv, file_name="shopify_products.csv", mime="text/csv")

import streamlit as st
import pandas as pd
import time
import json
import re
import asyncio
import io
import requests
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Price Scraper",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

.stApp {
    background: #0a0a0f;
    color: #e8e8f0;
}

section[data-testid="stSidebar"] {
    background: #0f0f1a;
    border-right: 1px solid #1e1e2e;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
}

.title-block {
    padding: 2rem 0 1rem 0;
    border-bottom: 2px solid #2a2a3e;
    margin-bottom: 2rem;
}

.title-block h1 {
    font-size: 2.8rem;
    background: linear-gradient(135deg, #7c6af7, #f763a8, #f7a763);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    line-height: 1.1;
}

.title-block p {
    color: #6b6b8a;
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    margin-top: 0.5rem;
}

.cadena-badge {
    display: inline-block;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.metric-card {
    background: #0f0f1a;
    border: 1px solid #1e1e2e;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
}

.metric-card .value {
    font-size: 2rem;
    font-weight: 800;
    color: #7c6af7;
    font-family: 'Space Mono', monospace;
}

.metric-card .label {
    font-size: 0.75rem;
    color: #6b6b8a;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.3rem;
}

.stButton > button {
    background: linear-gradient(135deg, #7c6af7, #f763a8);
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    padding: 0.6rem 2rem;
    width: 100%;
    transition: opacity 0.2s;
}

.stButton > button:hover {
    opacity: 0.85;
}

.stTextArea textarea {
    background: #0f0f1a;
    border: 1px solid #2a2a3e;
    color: #e8e8f0;
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    border-radius: 8px;
}

.stMultiSelect > div {
    background: #0f0f1a;
    border: 1px solid #2a2a3e;
    border-radius: 8px;
}

.stFileUploader {
    background: #0f0f1a;
    border: 1px dashed #2a2a3e;
    border-radius: 8px;
}

.stDataFrame {
    border: 1px solid #1e1e2e;
    border-radius: 8px;
    overflow: hidden;
}

.warning-box {
    background: #1a1400;
    border: 1px solid #3a2e00;
    border-left: 4px solid #f7a763;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 1rem 0;
    font-size: 0.85rem;
    color: #c9a84c;
    font-family: 'Space Mono', monospace;
}

.info-box {
    background: #0a0f1a;
    border: 1px solid #1e2a3e;
    border-left: 4px solid #7c6af7;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 1rem 0;
    font-size: 0.85rem;
    color: #8888bb;
    font-family: 'Space Mono', monospace;
}

div[data-testid="stExpander"] {
    background: #0f0f1a;
    border: 1px solid #1e1e2e;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SCRAPERS
# ─────────────────────────────────────────────


def scrape_ahumada(codigos, progress_cb=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9",
        "Referer": "https://www.farmaciasahumada.cl/"
    }
    resultados = []
    for i, codigo in enumerate(codigos):
        if progress_cb:
            progress_cb(i, len(codigos), codigo)
        url = f"https://www.farmaciasahumada.cl/{codigo}.html"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                scripts = soup.find_all("script", type="application/ld+json")
                producto_data = None
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if data.get("@type") == "Product":
                            producto_data = data
                            break
                    except:
                        continue
                if producto_data:
                    nombre = producto_data.get("name", "Sin nombre")
                    offer = producto_data.get("offers", {})
                    precio_jsonld = int(float(offer.get("price", 0)))
                    en_stock = "InStock" in offer.get("availability", "")
                    precio_normal = None
                    strike = soup.find("span", class_="strike-through")
                    if strike:
                        value_span = strike.find("span", class_="value")
                        if value_span and value_span.get("content"):
                            precio_normal = int(float(value_span["content"]))
                    if precio_normal:
                        precio_promo_final = precio_jsonld if precio_jsonld < precio_normal else None
                    else:
                        precio_normal = precio_jsonld
                        precio_promo_final = None
                    resultados.append({
                        "Cadena": "Ahumada", "SKU": codigo, "Producto": nombre,
                        "Precio_Normal": precio_normal, "Precio_Promo": precio_promo_final, "En_Stock": en_stock
                    })
        except Exception as e:
            resultados.append({"Cadena": "Ahumada", "SKU": codigo, "Producto": f"ERROR: {e}",
                              "Precio_Normal": 0, "Precio_Promo": None, "En_Stock": False})
        time.sleep(1.5)
    return pd.DataFrame(resultados)


def scrape_cruzverde(codigos, connect_sid, progress_cb=None):
    cookies = {"connect.sid": connect_sid}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.cruzverde.cl",
        "Referer": "https://www.cruzverde.cl/"
    }
    resultados = []
    for i, codigo in enumerate(codigos):
        if progress_cb:
            progress_cb(i, len(codigos), codigo)
        url = f"https://api.cruzverde.cl/product-service/products/detail/{codigo}"
        params = {"inventoryId": "Zonapañales1119"}
        try:
            r = requests.get(url, headers=headers, params=params,
                             cookies=cookies, timeout=10)
            if r.status_code == 200:
                datos = r.json()
                producto = datos.get("productData", {})
                if producto:
                    prices = producto.get("prices", {})
                    precio_normal = prices.get("price-list-cl", 0)
                    precio_oferta = prices.get("price-sale-cl", 0)
                    resultados.append({
                        "Cadena": "Cruz Verde", "SKU": codigo,
                        "Producto": producto.get("name", "Sin nombre"),
                        "Precio_Normal": precio_normal,
                        "Precio_Promo": precio_oferta if precio_oferta and precio_oferta < precio_normal else None,
                        "En_Stock": producto.get("stock", 0) > 0
                    })
            elif r.status_code == 401:
                resultados.append({"Cadena": "Cruz Verde", "SKU": codigo, "Producto": "ERROR: Cookie expirada",
                                  "Precio_Normal": 0, "Precio_Promo": None, "En_Stock": False})
        except Exception as e:
            resultados.append({"Cadena": "Cruz Verde", "SKU": codigo, "Producto": f"ERROR: {e}",
                              "Precio_Normal": 0, "Precio_Promo": None, "En_Stock": False})
        time.sleep(1.5)
    return pd.DataFrame(resultados)


def scrape_jumbo(skus, progress_cb=None):
    api_key = "key_JopvNXKS61kwGkBe"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json"}
    resultados = []
    for i, sku in enumerate(skus):
        if progress_cb:
            progress_cb(i, len(skus), sku)
        url = f"https://pwcdauseo-zone.cnstrc.com/search/{sku}"
        params = {"key": api_key, "c": "ciojs-2.1368.5"}
        try:
            r = requests.get(url, headers=headers, params=params, timeout=10)
            if r.status_code == 200:
                datos = r.json()
                lista = datos.get('response', {}).get('results', [])
                if lista:
                    producto_raiz = lista[0]
                    nombre = producto_raiz.get('value', 'Sin nombre')
                    variaciones = producto_raiz.get('variations', [])
                    precio_normal = precio_oferta = 0
                    en_stock = False
                    for var in variaciones:
                        d = var.get('data', {})
                        if d.get('storeId') == 'jumbocl':
                            precio_normal = d.get('listPrice', 0)
                            precio_oferta = d.get('sellingPrice', 0)
                            en_stock = not d.get('outOfStock', True)
                            break
                    if not precio_normal and variaciones:
                        d = variaciones[0].get('data', {})
                        precio_normal = d.get('listPrice', 0)
                        precio_oferta = d.get('sellingPrice', 0)
                        en_stock = not d.get('outOfStock', True)
                    resultados.append({
                        "Cadena": "Jumbo", "SKU": sku, "Producto": nombre,
                        "Precio_Normal": precio_normal,
                        "Precio_Promo": precio_oferta if precio_oferta < precio_normal else None,
                        "En_Stock": en_stock
                    })
        except Exception as e:
            resultados.append({"Cadena": "Jumbo", "SKU": sku, "Producto": f"ERROR: {e}",
                              "Precio_Normal": 0, "Precio_Promo": None, "En_Stock": False})
        time.sleep(1.5)
    return pd.DataFrame(resultados)


def scrape_preunic(skus, progress_cb=None):
    url = "https://7gdqzike3q-dsn.algolia.net/1/indexes/*/queries"
    params = {
        "x-algolia-agent": "Algolia for JavaScript (4.24.0); Browser (lite); instantsearch.js (4.74.0); react (18.3.1); react-instantsearch (7.13.0); react-instantsearch-core (7.13.0); next.js (14.2.32); JS Helper (3.22.4)",
        "x-algolia-api-key": "dcb263ac3f5bb5b523aad2f8c6029f7f",
        "x-algolia-application-id": "7GDQZIKE3Q"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "*/*", "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://preunic.cl", "Referer": "https://preunic.cl/"
    }
    resultados = []
    for i, sku in enumerate(skus):
        if progress_cb:
            progress_cb(i, len(skus), sku)
        body = json.dumps({"requests": [{"indexName": "Ecommerce-Products_production",
                                         "params": f"clickAnalytics=true&facets=%5B%22brand%22%2C%22categories.lvl0%22%2C%22has_promotions%22%2C%22has_sb_promotions%22%5D&filters=(communes%3A%22340%22%20OR%20zones%3A%2239%22%20OR%20store_exclusive%3Afalse)%20AND%20state%3Aactive&hitsPerPage=24&page=0&query={sku}"}]})
        try:
            r = requests.post(url, headers=headers,
                              params=params, data=body, timeout=10)
            if r.status_code == 200:
                hits = r.json().get('results', [{}])[0].get('hits', [])
                producto = next((h for h in hits if str(
                    h.get('sku')) == str(sku)), hits[0] if hits else None)
                if producto:
                    precio_normal = producto.get('price', 0)
                    precio_oferta = producto.get('offer_price', 0)
                    precio_tarjeta = producto.get('card_price', 0)
                    mejor_promo = None
                    if precio_oferta and precio_oferta < precio_normal:
                        mejor_promo = precio_oferta
                    if precio_tarjeta and precio_tarjeta < precio_normal:
                        mejor_promo = precio_tarjeta
                    resultados.append({
                        "Cadena": "Preunic", "SKU": sku, "Producto": producto.get('name', 'Sin nombre'),
                        "Precio_Normal": precio_normal, "Precio_Promo": mejor_promo,
                        "En_Stock": producto.get('state') == 'active'
                    })
        except Exception as e:
            resultados.append({"Cadena": "Preunic", "SKU": sku, "Producto": f"ERROR: {e}",
                              "Precio_Normal": 0, "Precio_Promo": None, "En_Stock": False})
        time.sleep(1.5)
    return pd.DataFrame(resultados)


def scrape_santaisabel(skus, progress_cb=None):
    url = "https://be-reg-groceries-bff-sisa.ecomm.cencosud.com/catalog/plp"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json", "Accept": "application/json",
        "ApiKey": "be-reg-groceries-sisa-catalog-wdhhq5a2fken"
    }
    resultados = []
    for i, sku in enumerate(skus):
        if progress_cb:
            progress_cb(i, len(skus), sku)
        payload = {"store": "pedrofontova", "collections": [], "fullText": sku,
                   "hideUnavailableItems": False, "brands": [], "from": 0, "to": 40,
                   "orderBy": "", "promotionalCards": False, "selectedFacets": [], "sponsoredProducts": True}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=10)
            if r.status_code == 200:
                productos = r.json().get('products', [])
                if productos:
                    items = productos[0].get('items', [])
                    if items:
                        item = items[0]
                        precio_normal = item.get('listPrice', 0)
                        precio_oferta = item.get('price', 0)
                        resultados.append({
                            "Cadena": "Santa Isabel", "SKU": sku, "Producto": item.get('name', 'Sin nombre'),
                            "Precio_Normal": precio_normal,
                            "Precio_Promo": precio_oferta if precio_oferta < precio_normal else None,
                            "En_Stock": item.get('stock', False)
                        })
        except Exception as e:
            resultados.append({"Cadena": "Santa Isabel", "SKU": sku, "Producto": f"ERROR: {e}",
                              "Precio_Normal": 0, "Precio_Promo": None, "En_Stock": False})
        time.sleep(1)
    return pd.DataFrame(resultados)


def scrape_unimarc(ref_ids, progress_cb=None):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=Service(
            ChromeDriverManager().install()), options=chrome_options)
        driver.get("https://www.unimarc.cl")
        time.sleep(4)
        cookies = {c['name']: c['value'] for c in driver.get_cookies()}
        anonymous = cookies.get('sessionAnonymousId', '')
        session_tok = cookies.get('sessionNanoId', '')
        driver.quit()
    except Exception as e:
        return pd.DataFrame([{"Cadena": "Unimarc", "SKU": rid, "Producto": f"ERROR Selenium: {e}", "Precio_Normal": 0, "Precio_Promo": None, "En_Stock": False} for rid in ref_ids])

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*", "Content-Type": "application/json",
        "Origin": "https://www.unimarc.cl", "Referer": "https://www.unimarc.cl/",
        "channel": "UNIMARC", "source": "web", "version": "1.0.0",
        "anonymous": anonymous, "session": session_tok,
    }
    resultados = []
    for i, ref_id in enumerate(ref_ids):
        if progress_cb:
            progress_cb(i, len(ref_ids), ref_id)
        body = {"from": "0", "orderBy": "", "searching": ref_id.lower(
        ), "promotionsOnly": False, "to": "49", "userTriggered": True}
        try:
            r = requests.post("https://bff-unimarc-ecommerce.unimarc.cl/catalog/product/search",
                              headers=headers, json=body, timeout=10)
            if r.status_code == 200:
                productos = r.json().get('availableProducts', [])
                if productos:
                    producto = next((p for p in productos if p.get('item', {}).get(
                        'refId', '').upper() == ref_id.upper()), productos[0])
                    item = producto.get('item', {})
                    price = producto.get('price', {})
                    precio_normal = int(
                        re.sub(r'[^\d]', '', price.get('listPrice', '0') or '0'))
                    precio_oferta = int(
                        re.sub(r'[^\d]', '', price.get('price', '0') or '0'))
                    en_oferta = price.get('inOffer', False)
                    resultados.append({
                        "Cadena": "Unimarc", "SKU": ref_id, "Producto": item.get('nameComplete', 'Sin nombre'),
                        "Precio_Normal": precio_normal,
                        "Precio_Promo": precio_oferta if en_oferta and precio_oferta < precio_normal else None,
                        "En_Stock": price.get('availableQuantity', 0) > 0
                    })
        except Exception as e:
            resultados.append({"Cadena": "Unimarc", "SKU": ref_id, "Producto": f"ERROR: {e}",
                              "Precio_Normal": 0, "Precio_Promo": None, "En_Stock": False})
        time.sleep(1.5)
    return pd.DataFrame(resultados)


def scrape_tottus(codigos, progress_cb=None):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            "--disable-blink-features=AutomationDetection")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")
        driver = webdriver.Chrome(service=Service(
            ChromeDriverManager().install()), options=chrome_options)
    except Exception as e:
        return pd.DataFrame([{"Cadena": "Tottus", "SKU": c, "Producto": f"ERROR Selenium: {e}", "Precio_Normal": 0, "Precio_Promo": None, "En_Stock": False} for c in codigos])

    resultados = []
    for i, codigo in enumerate(codigos):
        if progress_cb:
            progress_cb(i, len(codigos), codigo)
        try:
            driver.get(f"https://www.tottus.cl/tottus-cl/buscar?Ntt={codigo}")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "script[type='application/ld+json']")))
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            scripts = soup.find_all("script", type="application/ld+json")
            producto_data = None
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if data.get("@type") == "Product":
                        producto_data = data
                        break
                except:
                    continue
            if producto_data:
                offers = producto_data.get("offers", [])
                precios = sorted([int(o.get("price", 0))
                                 for o in offers if o.get("price")])
                resultados.append({
                    "Cadena": "Tottus", "SKU": codigo, "Producto": producto_data.get("name", "Sin nombre"),
                    "Precio_Normal": max(precios) if precios else 0,
                    "Precio_Promo": min(precios) if len(precios) > 1 else None,
                    "En_Stock": any("InStock" in o.get("availability", "") for o in offers)
                })
        except Exception as e:
            resultados.append({"Cadena": "Tottus", "SKU": codigo, "Producto": f"ERROR: {e}",
                              "Precio_Normal": 0, "Precio_Promo": None, "En_Stock": False})
        time.sleep(2)
    driver.quit()
    return pd.DataFrame(resultados)


def scrape_salcobrand(skus, progress_cb=None):
    try:
        import asyncio
        from playwright.sync_api import sync_playwright

        resultados = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
            page = context.new_page()
            page.goto("https://salcobrand.cl/", wait_until="networkidle")
            time.sleep(2)
            for i, sku in enumerate(skus):
                if progress_cb:
                    progress_cb(i, len(skus), sku)
                api_url = f"https://api.retailrocket.net/api/1.0/partner/602bba6097a5281b4cc438c9/items/?itemsIds={sku}&format=json"
                try:
                    respuesta = page.evaluate(
                        f"fetch('{api_url}').then(res => res.json())")
                    if respuesta and len(respuesta) > 0:
                        item = respuesta[0]
                        precio_actual = item.get('Price', 0)
                        precio_viejo = item.get('OldPrice', 0)
                        p_normal = precio_viejo if precio_viejo > 0 else precio_actual
                        p_promo = precio_actual if precio_viejo > 0 else None
                        resultados.append({
                            "Cadena": "Salcobrand", "SKU": sku, "Producto": item.get('Name', 'No encontrado'),
                            "Precio_Normal": p_normal, "Precio_Promo": p_promo,
                            "En_Stock": item.get('IsAvailable', False)
                        })
                    else:
                        resultados.append({"Cadena": "Salcobrand", "SKU": sku, "Producto": "No encontrado",
                                          "Precio_Normal": 0, "Precio_Promo": None, "En_Stock": False})
                except Exception as e:
                    resultados.append({"Cadena": "Salcobrand", "SKU": sku, "Producto": f"ERROR: {e}",
                                      "Precio_Normal": 0, "Precio_Promo": None, "En_Stock": False})
                time.sleep(1)
            browser.close()
        return pd.DataFrame(resultados)
    except Exception as e:
        return pd.DataFrame([{"Cadena": "Salcobrand", "SKU": sku, "Producto": f"ERROR Playwright: {e}", "Precio_Normal": 0, "Precio_Promo": None, "En_Stock": False} for sku in skus])


def scrape_walmart(skus, progress_cb=None):
    try:
        from playwright.sync_api import sync_playwright

        resultados = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = context.new_page()
            for i, sku in enumerate(skus):
                if progress_cb:
                    progress_cb(i, len(skus), sku)
                try:
                    page.goto(
                        f"https://super.lider.cl/ip/{sku}", wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(3000)
                    json_raw = page.evaluate(
                        'document.getElementById("__NEXT_DATA__").innerText')
                    data = json.loads(json_raw)
                    base_product = data['props']['pageProps']['initialData']['data']['product']
                    nombre = base_product.get('name', 'Sin nombre')
                    price_info = base_product.get('priceInfo', {})
                    p_actual = price_info.get(
                        'currentPrice', {}).get('price', 0)
                    p_anterior = price_info.get('wasPrice', {}).get('price', 0)
                    if p_anterior and p_anterior > 0:
                        precio_normal = p_anterior
                        precio_oferta = p_actual
                    else:
                        precio_normal = p_actual
                        precio_oferta = None
                    resultados.append({
                        "Cadena": "Walmart/Lider", "SKU": sku, "Producto": nombre,
                        "Precio_Normal": precio_normal, "Precio_Promo": precio_oferta,
                        "En_Stock": base_product.get('inventory', {}).get('isAvailable', False)
                    })
                except Exception as e:
                    resultados.append({"Cadena": "Walmart/Lider", "SKU": sku, "Producto": f"ERROR: {e}",
                                      "Precio_Normal": 0, "Precio_Promo": None, "En_Stock": False})
            browser.close()
        return pd.DataFrame(resultados)
    except Exception as e:
        return pd.DataFrame([{"Cadena": "Walmart/Lider", "SKU": sku, "Producto": f"ERROR Playwright: {e}", "Precio_Normal": 0, "Precio_Promo": None, "En_Stock": False} for sku in skus])


# ─────────────────────────────────────────────
# CADENA CONFIG
# ─────────────────────────────────────────────
CADENAS = {
    "Ahumada": {"color": "#e63946", "emoji": "💊", "sku_label": "Código (ej: 72820)", "necesita_cookie": False},
    "Cruz Verde": {"color": "#2a9d8f", "emoji": "🟢", "sku_label": "Código (ej: 579721)", "necesita_cookie": True},
    "Jumbo": {"color": "#e76f51", "emoji": "🛒", "sku_label": "SKU (ej: 1933911)", "necesita_cookie": False},
    "Preunic": {"color": "#f4a261", "emoji": "🏪", "sku_label": "SKU (ej: 584056)", "necesita_cookie": False},
    "Salcobrand": {"color": "#457b9d", "emoji": "💙", "sku_label": "SKU (ej: 592919)", "necesita_cookie": False},
    "Santa Isabel": {"color": "#e9c46a", "emoji": "🌟", "sku_label": "SKU (ej: 996166)", "necesita_cookie": False},
    "Tottus": {"color": "#e63946", "emoji": "🔴", "sku_label": "Código tienda (ej: 20547253)", "necesita_cookie": False},
    "Unimarc": {"color": "#6a4c93", "emoji": "🟣", "sku_label": "Ref ID (ej: 000000000000650823-UN)", "necesita_cookie": False},
    "Walmart/Lider": {"color": "#1d3557", "emoji": "💛", "sku_label": "SKU (ej: 00779464017072)", "necesita_cookie": False},
}

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛒 Price Scraper")
    st.markdown("---")

    cadenas_seleccionadas = st.multiselect(
        "Selecciona cadenas",
        options=list(CADENAS.keys()),
        default=["Jumbo"]
    )

    st.markdown("---")
    st.markdown("#### 🔑 Cruz Verde Cookie")
    connect_sid = st.text_input(
        "connect.sid",
        type="password",
        placeholder="Pega aquí tu cookie",
        help="F12 → Application → Cookies → www.cruzverde.cl → connect.sid"
    )
    if "Cruz Verde" in cadenas_seleccionadas and not connect_sid:
        st.markdown(
            '<div class="warning-box">⚠️ Cruz Verde requiere cookie manual</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p style="color:#6b6b8a;font-size:0.75rem;font-family:\'Space Mono\',monospace;">Price Scraper v1.0<br>9 cadenas • Chile</p>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
st.markdown("""
<div class="title-block">
    <h1>Price Scraper 🛒</h1>
    <p>// extracción de precios · 9 cadenas · Chile</p>
</div>
""", unsafe_allow_html=True)

if not cadenas_seleccionadas:
    st.info("👈 Selecciona al menos una cadena en el panel izquierdo para comenzar.")
    st.stop()

# ─── SKU INPUT ───
st.markdown("### 📋 Ingresa los SKUs")

tab1, tab2 = st.tabs(["✏️ Ingresar manualmente", "📁 Cargar desde archivo"])

skus_manuales = []
skus_archivo = []

with tab1:
    for cadena in cadenas_seleccionadas:
        cfg = CADENAS[cadena]
        st.markdown(f"**{cfg['emoji']} {cadena}** — `{cfg['sku_label']}`")
        texto = st.text_area(
            f"SKUs para {cadena}",
            placeholder="Un SKU por línea",
            key=f"manual_{cadena}",
            height=100,
            label_visibility="collapsed"
        )
        if texto.strip():
            skus_manuales.append(
                (cadena, [s.strip() for s in texto.strip().splitlines() if s.strip()]))

with tab2:
    st.markdown('<div class="info-box">📌 El archivo debe tener una columna llamada <b>SKU</b> y otra llamada <b>Cadena</b></div>', unsafe_allow_html=True)
    archivo = st.file_uploader("Sube tu Excel o CSV", type=["xlsx", "csv"])
    if archivo:
        try:
            if archivo.name.endswith(".csv"):
                df_upload = pd.read_csv(archivo)
            else:
                df_upload = pd.read_excel(archivo)

            if "SKU" in df_upload.columns and "Cadena" in df_upload.columns:
                for cadena in cadenas_seleccionadas:
                    skus_cadena = df_upload[df_upload["Cadena"].str.lower(
                    ) == cadena.lower()]["SKU"].astype(str).tolist()
                    if skus_cadena:
                        skus_archivo.append((cadena, skus_cadena))
                st.success(f"✅ {len(df_upload)} filas cargadas correctamente")
                st.dataframe(df_upload.head(5), use_container_width=True)
            else:
                st.error("❌ El archivo debe tener columnas 'SKU' y 'Cadena'")
        except Exception as e:
            st.error(f"❌ Error leyendo archivo: {e}")

# Combinamos SKUs de ambas fuentes
todos_skus = {}
for cadena, skus in skus_manuales + skus_archivo:
    if cadena not in todos_skus:
        todos_skus[cadena] = []
    todos_skus[cadena].extend(skus)
# Deduplicamos
for cadena in todos_skus:
    todos_skus[cadena] = list(dict.fromkeys(todos_skus[cadena]))

# Resumen
if todos_skus:
    st.markdown("### 📊 Resumen")
    cols = st.columns(len(todos_skus))
    for i, (cadena, skus) in enumerate(todos_skus.items()):
        cfg = CADENAS.get(cadena, {})
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="value">{len(skus)}</div>
                <div class="label">{cfg.get('emoji', '')} {cadena}</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# ─── RUN BUTTON ───
if st.button("🚀 Iniciar extracción", disabled=not todos_skus):
    resultados_totales = []
    errores = []

    for cadena, skus in todos_skus.items():
        if not skus:
            continue

        st.markdown(
            f"#### {CADENAS[cadena]['emoji']} Procesando **{cadena}** ({len(skus)} SKUs)...")
        progress_bar = st.progress(0)
        status_text = st.empty()

        def make_progress(pb, st_text):
            def cb(i, total, sku):
                pb.progress((i + 1) / total)
                st_text.markdown(
                    f'<p style="color:#6b6b8a;font-size:0.8rem;font-family:\'Space Mono\',monospace;">→ {sku}</p>', unsafe_allow_html=True)
            return cb

        progress_cb = make_progress(progress_bar, status_text)

        try:
            if cadena == "Ahumada":
                df = scrape_ahumada(skus, progress_cb)
            elif cadena == "Cruz Verde":
                if not connect_sid:
                    st.error(
                        "❌ Cruz Verde requiere la cookie connect.sid en el panel izquierdo.")
                    continue
                df = scrape_cruzverde(skus, connect_sid, progress_cb)
            elif cadena == "Jumbo":
                df = scrape_jumbo(skus, progress_cb)
            elif cadena == "Preunic":
                df = scrape_preunic(skus, progress_cb)
            elif cadena == "Salcobrand":
                df = scrape_salcobrand(skus, progress_cb)
            elif cadena == "Santa Isabel":
                df = scrape_santaisabel(skus, progress_cb)
            elif cadena == "Tottus":
                df = scrape_tottus(skus, progress_cb)
            elif cadena == "Unimarc":
                df = scrape_unimarc(skus, progress_cb)
            elif cadena == "Walmart/Lider":
                df = scrape_walmart(skus, progress_cb)
            else:
                continue

            progress_bar.progress(1.0)
            status_text.markdown(
                f'<p style="color:#2a9d8f;font-size:0.8rem;font-family:\'Space Mono\',monospace;">✅ Completado</p>', unsafe_allow_html=True)

            if df is not None and not df.empty:
                resultados_totales.append(df)

        except Exception as e:
            st.error(f"❌ Error en {cadena}: {e}")

    if resultados_totales:
        df_final = pd.concat(resultados_totales, ignore_index=True)

        st.markdown("---")
        st.markdown("### ✅ Resultados")

        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(
                f'<div class="metric-card"><div class="value">{len(df_final)}</div><div class="label">Total productos</div></div>', unsafe_allow_html=True)
        with col2:
            con_promo = df_final["Precio_Promo"].notna().sum()
            st.markdown(
                f'<div class="metric-card"><div class="value">{con_promo}</div><div class="label">Con promoción</div></div>', unsafe_allow_html=True)
        with col3:
            en_stock = df_final["En_Stock"].sum(
            ) if "En_Stock" in df_final.columns else 0
            st.markdown(
                f'<div class="metric-card"><div class="value">{en_stock}</div><div class="label">En stock</div></div>', unsafe_allow_html=True)
        with col4:
            cadenas_unicas = df_final["Cadena"].nunique()
            st.markdown(
                f'<div class="metric-card"><div class="value">{cadenas_unicas}</div><div class="label">Cadenas</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(df_final, use_container_width=True, height=400)

        # Descargas
        st.markdown("### 💾 Descargar resultados")
        col_csv, col_excel = st.columns(2)

        with col_csv:
            csv = df_final.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                "⬇️ Descargar CSV",
                data=csv,
                file_name=f"precios_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col_excel:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_final.to_excel(writer, index=False, sheet_name="Precios")
            st.download_button(
                "⬇️ Descargar Excel",
                data=buffer.getvalue(),
                file_name=f"precios_{time.strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        st.warning("⚠️ No se obtuvieron resultados.")

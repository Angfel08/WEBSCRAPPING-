import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import pandas as pd
import time
import json
import re
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─────────────────────────────────────────────
# CONFIGURACIÓN DRIVERS
# ─────────────────────────────────────────────
EDGEDRIVER_PATH = r"C:\Users\afr4d3844\OneDrive - Haleon\DEMANDA CHILE - TOOLS DIEGO\Category Management\Scrapers\NO BORRAR\chromedriver-win64\msedgedriver.exe"

EDGE_BINARY = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE_BINARY):
    EDGE_BINARY = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

# ─────────────────────────────────────────────
# TEMA
# ─────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ─────────────────────────────────────────────
# SCRAPERS
# ─────────────────────────────────────────────

def scrape_ahumada(codigos, log):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9",
        "Referer": "https://www.farmaciasahumada.cl/"
    }
    resultados = []
    for codigo in codigos:
        log(f"  [Ahumada] Procesando: {codigo}")
        url = f"https://www.farmaciasahumada.cl/{codigo}.html"
        try:
            r = requests.get(url, headers=headers, timeout=10, verify=False)
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
                    resultados.append({"Cadena": "Ahumada", "SKU": codigo, "Producto": nombre,
                                       "Precio_Normal": precio_normal, "Precio_Promo": precio_promo_final, "En_Stock": en_stock})
                    log(f"  ✅ {nombre} | ${precio_normal}")
                else:
                    log(f"  ⚠️ {codigo} no encontrado")
            else:
                log(f"  ❌ Error {r.status_code} con {codigo}")
        except Exception as e:
            log(f"  ❌ Error: {e}")
        time.sleep(1.5)
    return pd.DataFrame(resultados)


def scrape_cruzverde(codigos, connect_sid, log):
    cookies = {"connect.sid": connect_sid}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.cruzverde.cl",
        "Referer": "https://www.cruzverde.cl/"
    }
    resultados = []
    for codigo in codigos:
        log(f"  [Cruz Verde] Procesando: {codigo}")
        url = f"https://api.cruzverde.cl/product-service/products/detail/{codigo}"
        params = {"inventoryId": "Zonapañales1119"}
        try:
            r = requests.get(url, headers=headers, params=params,
                             cookies=cookies, timeout=10, verify=False)
            if r.status_code == 200:
                datos = r.json()
                producto = datos.get("productData", {})
                if producto:
                    prices = producto.get("prices", {})
                    precio_normal = prices.get("price-list-cl", 0)
                    precio_oferta = prices.get("price-sale-cl", 0)
                    resultados.append({"Cadena": "Cruz Verde", "SKU": codigo,
                                       "Producto": producto.get("name", "Sin nombre"),
                                       "Precio_Normal": precio_normal,
                                       "Precio_Promo": precio_oferta if precio_oferta and precio_oferta < precio_normal else None,
                                       "En_Stock": producto.get("stock", 0) > 0})
                    log(f"  ✅ {producto.get('name')} | ${precio_normal}")
            elif r.status_code == 401:
                log(f"  ❌ Cookie expirada para {codigo}")
            else:
                log(f"  ❌ Error {r.status_code} con {codigo}")
        except Exception as e:
            log(f"  ❌ Error: {e}")
        time.sleep(1.5)
    return pd.DataFrame(resultados)


def scrape_jumbo(skus, log):
    api_key = "key_JopvNXKS61kwGkBe"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json"}
    resultados = []
    for sku in skus:
        log(f"  [Jumbo] Procesando: {sku}")
        url = f"https://pwcdauseo-zone.cnstrc.com/search/{sku}"
        params = {"key": api_key, "c": "ciojs-2.1368.5"}
        try:
            r = requests.get(url, headers=headers, params=params, timeout=10, verify=False)
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
                    resultados.append({"Cadena": "Jumbo", "SKU": sku, "Producto": nombre,
                                       "Precio_Normal": precio_normal,
                                       "Precio_Promo": precio_oferta if precio_oferta < precio_normal else None,
                                       "En_Stock": en_stock})
                    log(f"  ✅ {nombre} | ${precio_normal}")
                else:
                    log(f"  ⚠️ {sku} no encontrado")
            else:
                log(f"  ❌ Error {r.status_code} con {sku}")
        except Exception as e:
            log(f"  ❌ Error: {e}")
        time.sleep(1.5)
    return pd.DataFrame(resultados)


def scrape_preunic(skus, log):
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
    for sku in skus:
        log(f"  [Preunic] Procesando: {sku}")
        body = json.dumps({"requests": [{"indexName": "Ecommerce-Products_production",
                                         "params": f"clickAnalytics=true&facets=%5B%22brand%22%2C%22categories.lvl0%22%2C%22has_promotions%22%2C%22has_sb_promotions%22%5D&filters=(communes%3A%22340%22%20OR%20zones%3A%2239%22%20OR%20store_exclusive%3Afalse)%20AND%20state%3Aactive&hitsPerPage=24&page=0&query={sku}"}]})
        try:
            r = requests.post(url, headers=headers, params=params, data=body, timeout=10, verify=False)
            if r.status_code == 200:
                hits = r.json().get('results', [{}])[0].get('hits', [])
                producto = next((h for h in hits if str(h.get('sku')) == str(sku)), hits[0] if hits else None)
                if producto:
                    precio_normal = producto.get('price', 0)
                    precio_oferta = producto.get('offer_price', 0)
                    mejor_promo = precio_oferta if precio_oferta and precio_oferta < precio_normal else None
                    resultados.append({"Cadena": "Preunic", "SKU": sku, "Producto": producto.get('name', 'Sin nombre'),
                                       "Precio_Normal": precio_normal, "Precio_Promo": mejor_promo,
                                       "En_Stock": producto.get('state') == 'active'})
                    log(f"  ✅ {producto.get('name')} | ${precio_normal}")
                else:
                    log(f"  ⚠️ {sku} no encontrado")
            else:
                log(f"  ❌ Error {r.status_code} con {sku}")
        except Exception as e:
            log(f"  ❌ Error: {e}")
        time.sleep(1.5)
    return pd.DataFrame(resultados)


def scrape_santaisabel(skus, log):
    url = "https://be-reg-groceries-bff-sisa.ecomm.cencosud.com/catalog/plp"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json", "Accept": "application/json",
        "ApiKey": "be-reg-groceries-sisa-catalog-wdhhq5a2fken"
    }
    resultados = []
    for sku in skus:
        log(f"  [Santa Isabel] Procesando: {sku}")
        payload = {"store": "pedrofontova", "collections": [], "fullText": sku,
                   "hideUnavailableItems": False, "brands": [], "from": 0, "to": 40,
                   "orderBy": "", "promotionalCards": False, "selectedFacets": [], "sponsoredProducts": True}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=10, verify=False)
            if r.status_code == 200:
                productos = r.json().get('products', [])
                if productos:
                    items = productos[0].get('items', [])
                    if items:
                        item = items[0]
                        precio_normal = item.get('listPrice', 0)
                        precio_oferta = item.get('price', 0)
                        resultados.append({"Cadena": "Santa Isabel", "SKU": sku, "Producto": item.get('name', 'Sin nombre'),
                                           "Precio_Normal": precio_normal,
                                           "Precio_Promo": precio_oferta if precio_oferta < precio_normal else None,
                                           "En_Stock": item.get('stock', False)})
                        log(f"  ✅ {item.get('name')} | ${precio_normal}")
                    else:
                        log(f"  ⚠️ {sku} sin datos de precio")
                else:
                    log(f"  ⚠️ {sku} no encontrado")
            else:
                log(f"  ❌ Error {r.status_code} con {sku}")
        except Exception as e:
            log(f"  ❌ Error: {e}")
        time.sleep(1)
    return pd.DataFrame(resultados)


def scrape_unimarc(ref_ids, log):
    try:
        from selenium import webdriver
        from selenium.webdriver.edge.service import Service as EdgeService
        from selenium.webdriver.edge.options import Options as EdgeOptions

        log("  [Unimarc] Obteniendo tokens de sesión con Edge...")
        edge_options = EdgeOptions()
        edge_options.add_argument("--headless")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--disable-gpu")
        edge_options.binary_location = EDGE_BINARY

        driver = webdriver.Edge(service=EdgeService(EDGEDRIVER_PATH), options=edge_options)
        driver.get("https://www.unimarc.cl")
        time.sleep(4)
        cookies = {c['name']: c['value'] for c in driver.get_cookies()}
        anonymous = cookies.get('sessionAnonymousId', '')
        session_tok = cookies.get('sessionNanoId', '')
        driver.quit()
        log("  ✅ Tokens obtenidos")
    except Exception as e:
        log(f"  ❌ Error Edge: {e}")
        return pd.DataFrame()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*", "Content-Type": "application/json",
        "Origin": "https://www.unimarc.cl", "Referer": "https://www.unimarc.cl/",
        "channel": "UNIMARC", "source": "web", "version": "1.0.0",
        "anonymous": anonymous, "session": session_tok,
    }
    resultados = []
    for ref_id in ref_ids:
        log(f"  [Unimarc] Procesando: {ref_id}")
        body = {"from": "0", "orderBy": "", "searching": ref_id.lower(),
                "promotionsOnly": False, "to": "49", "userTriggered": True}
        try:
            r = requests.post("https://bff-unimarc-ecommerce.unimarc.cl/catalog/product/search",
                              headers=headers, json=body, timeout=10, verify=False)
            if r.status_code == 200:
                productos = r.json().get('availableProducts', [])
                if productos:
                    producto = next((p for p in productos if p.get('item', {}).get(
                        'refId', '').upper() == ref_id.upper()), productos[0])
                    item = producto.get('item', {})
                    price = producto.get('price', {})
                    precio_normal = int(re.sub(r'[^\d]', '', price.get('listPrice', '0') or '0'))
                    precio_oferta = int(re.sub(r'[^\d]', '', price.get('price', '0') or '0'))
                    en_oferta = price.get('inOffer', False)
                    resultados.append({"Cadena": "Unimarc", "SKU": ref_id,
                                       "Producto": item.get('nameComplete', 'Sin nombre'),
                                       "Precio_Normal": precio_normal,
                                       "Precio_Promo": precio_oferta if en_oferta and precio_oferta < precio_normal else None,
                                       "En_Stock": price.get('availableQuantity', 0) > 0})
                    log(f"  ✅ {item.get('nameComplete')} | ${precio_normal}")
                else:
                    log(f"  ⚠️ {ref_id} no encontrado")
            else:
                log(f"  ❌ Error {r.status_code} con {ref_id}")
        except Exception as e:
            log(f"  ❌ Error: {e}")
        time.sleep(1.5)
    return pd.DataFrame(resultados)


def scrape_tottus(codigos, log):
    try:
        from selenium import webdriver
        from selenium.webdriver.edge.service import Service as EdgeService
        from selenium.webdriver.edge.options import Options as EdgeOptions
        from selenium.webdriver.support.ui import WebDriverWait

        log("  [Tottus] Iniciando con Microsoft Edge...")
        edge_options = EdgeOptions()
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0"
        )
        edge_options.binary_location = EDGE_BINARY

        driver = webdriver.Edge(service=EdgeService(EDGEDRIVER_PATH), options=edge_options)
        driver.set_page_load_timeout(30)
    except Exception as e:
        log(f"  ❌ Error iniciando Edge: {e}")
        return pd.DataFrame()

    resultados = []
    for codigo in codigos:
        log(f"  [Tottus] Procesando: {codigo}...")
        url = f"https://www.tottus.cl/tottus-cl/buscar?Ntt={codigo}"
        try:
            driver.get(url)
            try:
                WebDriverWait(driver, 8).until(lambda d: "articulo" in d.current_url)
            except:
                log(f"  ⚠️ {codigo} — Producto no existe en Tottus")
                continue
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
                nombre = producto_data.get("name", "Sin nombre")
                offers = producto_data.get("offers", [])
                precios = sorted([int(o.get("price", 0)) for o in offers if o.get("price")])
                precio_normal = max(precios) if precios else 0
                precio_promo = min(precios) if len(precios) > 1 else None
                en_stock = any("InStock" in o.get("availability", "") for o in offers)
                resultados.append({"Cadena": "Tottus", "SKU": codigo, "Producto": nombre,
                                   "Precio_Normal": precio_normal, "Precio_Promo": precio_promo, "En_Stock": en_stock})
                log(f"  ✅ {nombre} | ${precio_normal}")
            else:
                log(f"  ⚠️ {codigo} — JSON-LD no encontrado")
        except Exception as e:
            log(f"  ❌ Error con {codigo}: {e}")
        time.sleep(1.5)

    try:
        driver.quit()
    except:
        pass
    return pd.DataFrame(resultados) if resultados else pd.DataFrame()


def scrape_salcobrand(skus, log):
    try:
        from playwright.sync_api import sync_playwright
        resultados = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
            page = context.new_page()
            log("  [Salcobrand] Sincronizando sesion...")
            page.goto("https://salcobrand.cl/", wait_until="networkidle")
            time.sleep(2)
            for sku in skus:
                log(f"  [Salcobrand] Procesando: {sku}")
                api_url = f"https://api.retailrocket.net/api/1.0/partner/602bba6097a5281b4cc438c9/items/?itemsIds={sku}&format=json"
                try:
                    respuesta = page.evaluate(f"fetch('{api_url}').then(res => res.json())")
                    if respuesta and len(respuesta) > 0:
                        item = respuesta[0]
                        precio_actual = item.get('Price', 0)
                        precio_viejo = item.get('OldPrice', 0)
                        p_normal = precio_viejo if precio_viejo > 0 else precio_actual
                        p_promo = precio_actual if precio_viejo > 0 else None
                        resultados.append({"Cadena": "Salcobrand", "SKU": sku,
                                           "Producto": item.get('Name', 'No encontrado'),
                                           "Precio_Normal": p_normal, "Precio_Promo": p_promo,
                                           "En_Stock": item.get('IsAvailable', False)})
                        log(f"  ✅ {item.get('Name')} | ${p_normal}")
                    else:
                        log(f"  ⚠️ {sku} no encontrado")
                except Exception as e:
                    log(f"  ❌ Error: {e}")
                time.sleep(1)
            browser.close()
        return pd.DataFrame(resultados)
    except Exception as e:
        log(f"  ❌ Error Playwright: {e}")
        return pd.DataFrame()


def scrape_walmart(skus, log):
    cookies_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.json")
    if not os.path.exists(cookies_path):
        log("  ❌ No se encontro cookies.json. Exporta las cookies de super.lider.cl con Cookie-Editor.")
        return pd.DataFrame()
    try:
        with open(cookies_path, "r") as f:
            raw = json.load(f)
        cookies = {c['name']: c['value'] for c in raw} if isinstance(raw, list) else raw
        log(f"  [Walmart] ✅ Cookies cargadas ({len(cookies)} cookies)")
    except Exception as e:
        log(f"  ❌ Error leyendo cookies.json: {e}")
        return pd.DataFrame()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-CL,es;q=0.9",
        "Referer": "https://super.lider.cl/"
    }
    resultados = []
    cookies_vencidas = False
    for sku in skus:
        log(f"  [Walmart] Procesando: {sku}")
        url = f"https://super.lider.cl/ip/{sku}"
        try:
            r = requests.get(url, headers=headers, cookies=cookies, timeout=15, verify=False)
            if "Robot o humano" in r.text or "Robot or human" in r.text or "__NEXT_DATA__" not in r.text:
                if not cookies_vencidas:
                    log("  ⚠️ Cookies vencidas. Vuelve a exportar con Cookie-Editor.")
                    cookies_vencidas = True
                log(f"  ❌ {sku} bloqueado por captcha")
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            next_data = soup.find("script", id="__NEXT_DATA__")
            if not next_data:
                log(f"  ❌ {sku} sin __NEXT_DATA__")
                continue
            data = json.loads(next_data.string)
            product = data.get('props', {}).get('pageProps', {}).get(
                'initialData', {}).get('data', {}).get('product')
            if not product:
                log(f"  ⚠️ {sku} — No disponible en web")
                continue
            nombre = product.get('name', 'Sin nombre')
            price_info = product.get('priceInfo', {}) or {}
            p_actual = (price_info.get('currentPrice') or {}).get('price', 0)
            p_anterior = (price_info.get('wasPrice') or {}).get('price', 0)
            precio_normal = p_anterior if p_anterior and p_anterior > 0 else p_actual
            precio_promo = p_actual if p_anterior and p_anterior > 0 else None
            resultados.append({"Cadena": "Walmart/Lider", "SKU": sku, "Producto": nombre,
                               "Precio_Normal": precio_normal, "Precio_Promo": precio_promo,
                               "En_Stock": product.get('inventory', {}).get('isAvailable', False)})
            log(f"  ✅ {nombre} | Normal: ${precio_normal} | Promo: ${precio_promo}")
        except Exception as e:
            log(f"  ❌ Error con {sku}: {e}")
        time.sleep(2)
    return pd.DataFrame(resultados)


# ─────────────────────────────────────────────
# GUI
# ─────────────────────────────────────────────

CADENAS = ["Ahumada", "Cruz Verde", "Jumbo", "Preunic",
           "Salcobrand", "Santa Isabel", "Tottus", "Unimarc", "Walmart/Lider"]

COLORES = {
    "bg": "#0f1117", "panel": "#1a1d27", "card": "#22263a",
    "accent": "#4f8ef7", "success": "#22c55e", "warning": "#f59e0b",
    "danger": "#ef4444", "text": "#e2e8f0", "muted": "#64748b", "border": "#2d3150",
}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Price Scraper")
        self.geometry("1100x750")
        self.minsize(900, 650)
        self.configure(fg_color=COLORES["bg"])
        self.df_resultado = None
        self.cadena_var = ctk.StringVar(value=CADENAS[0])
        self.connect_sid_var = ctk.StringVar()
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=COLORES["panel"], corner_radius=0, height=58)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="🛒", font=("Segoe UI Emoji", 22)).pack(side="left", padx=(20, 6), pady=14)
        ctk.CTkLabel(header, text="Price Scraper", font=ctk.CTkFont("Segoe UI", 17, "bold"),
                     text_color=COLORES["text"]).pack(side="left", pady=14)
        ctk.CTkLabel(header, text="9 cadenas  •  extraccion automatica de precios",
                     font=ctk.CTkFont("Segoe UI", 11), text_color=COLORES["muted"]).pack(side="left", padx=14, pady=14)

        self.status_var = ctk.StringVar(value="Listo")
        status_bar = ctk.CTkFrame(self, fg_color=COLORES["panel"], corner_radius=0, height=28)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        self.status_lbl = ctk.CTkLabel(status_bar, textvariable=self.status_var,
                                       font=ctk.CTkFont("Segoe UI", 10), text_color=COLORES["muted"], anchor="w")
        self.status_lbl.pack(side="left", padx=14)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.columnconfigure(0, weight=0, minsize=270)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        self._build_left(body)
        self._build_right(body)

    def _build_left(self, parent):
        left = ctk.CTkFrame(parent, fg_color=COLORES["panel"], corner_radius=12, width=270)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.pack_propagate(False)
        pad = {"padx": 16, "pady": (0, 10)}

        ctk.CTkLabel(left, text="Cadena", font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=COLORES["muted"]).pack(anchor="w", padx=16, pady=(16, 4))
        self.cadena_menu = ctk.CTkComboBox(left, variable=self.cadena_var, values=CADENAS,
                                           command=self._on_cadena_change, fg_color=COLORES["card"],
                                           border_color=COLORES["border"], button_color=COLORES["accent"],
                                           dropdown_fg_color=COLORES["card"],
                                           font=ctk.CTkFont("Segoe UI", 12), width=238)
        self.cadena_menu.pack(**pad)

        self.cookie_frame = ctk.CTkFrame(left, fg_color=COLORES["card"], corner_radius=8)
        ctk.CTkLabel(self.cookie_frame, text="🔑  Cookie Cruz Verde (connect.sid)",
                     font=ctk.CTkFont("Segoe UI", 10, "bold"), text_color=COLORES["warning"]).pack(anchor="w", padx=10, pady=(8, 2))
        self.cookie_entry = ctk.CTkEntry(self.cookie_frame, textvariable=self.connect_sid_var, show="*",
                                         fg_color=COLORES["panel"], border_color=COLORES["border"],
                                         font=ctk.CTkFont("Consolas", 10), width=218)
        self.cookie_entry.pack(padx=10, pady=(0, 8))

        ctk.CTkLabel(left, text="SKUs  (uno por linea)", font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=COLORES["muted"]).pack(anchor="w", padx=16, pady=(4, 4))
        self.sku_text = ctk.CTkTextbox(left, height=140, fg_color=COLORES["card"],
                                       border_color=COLORES["border"], font=ctk.CTkFont("Consolas", 11), width=238)
        self.sku_text.pack(**pad)

        ctk.CTkButton(left, text="📁  Cargar Excel / CSV", command=self._cargar_archivo,
                      fg_color=COLORES["card"], hover_color=COLORES["border"],
                      border_color=COLORES["accent"], border_width=1, text_color=COLORES["accent"],
                      font=ctk.CTkFont("Segoe UI", 11), width=238, height=34).pack(**pad)

        self.archivo_label = ctk.CTkLabel(left, text="", font=ctk.CTkFont("Segoe UI", 9),
                                          text_color=COLORES["success"], wraplength=240)
        self.archivo_label.pack(anchor="w", padx=16)

        ctk.CTkFrame(left, fg_color=COLORES["border"], height=1).pack(fill="x", padx=16, pady=10)

        self.btn_iniciar = ctk.CTkButton(left, text="🚀  Iniciar extraccion", command=self._iniciar,
                                         fg_color=COLORES["accent"], hover_color="#3a70d4",
                                         font=ctk.CTkFont("Segoe UI", 13, "bold"), width=238, height=42, corner_radius=8)
        self.btn_iniciar.pack(padx=16, pady=(0, 8))

        self.btn_base = ctk.CTkButton(left, text="⚡  Ejecutar skus_base.xlsx", command=self._iniciar_base,
                                      fg_color="#166534", hover_color="#14532d",
                                      font=ctk.CTkFont("Segoe UI", 12, "bold"), width=238, height=38, corner_radius=8)
        self.btn_base.pack(padx=16, pady=(0, 12))

        ctk.CTkFrame(left, fg_color=COLORES["border"], height=1).pack(fill="x", padx=16, pady=(0, 10))

        self.btn_csv = ctk.CTkButton(left, text="💾  Exportar CSV", command=self._exportar,
                                     fg_color=COLORES["card"], hover_color=COLORES["border"],
                                     border_color=COLORES["success"], border_width=1, text_color=COLORES["success"],
                                     font=ctk.CTkFont("Segoe UI", 11), width=238, height=34, state="disabled")
        self.btn_csv.pack(padx=16, pady=(0, 6))

        self.btn_xlsx = ctk.CTkButton(left, text="📊  Exportar Excel", command=self._exportar_xlsx,
                                      fg_color=COLORES["card"], hover_color=COLORES["border"],
                                      border_color=COLORES["success"], border_width=1, text_color=COLORES["success"],
                                      font=ctk.CTkFont("Segoe UI", 11), width=238, height=34, state="disabled")
        self.btn_xlsx.pack(padx=16, pady=(0, 16))

    def _build_right(self, parent):
        import tkinter.ttk as ttv
        import tkinter as tk

        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=0)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        log_frame = ctk.CTkFrame(right, fg_color=COLORES["panel"], corner_radius=12)
        log_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ctk.CTkLabel(log_frame, text="Log de extraccion", font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=COLORES["muted"]).pack(anchor="w", padx=14, pady=(10, 4))
        self.log_text = ctk.CTkTextbox(log_frame, height=160, fg_color="#0d1117", text_color="#4ade80",
                                       font=ctk.CTkFont("Consolas", 10), border_color=COLORES["border"])
        self.log_text.pack(fill="x", padx=12, pady=(0, 12))
        self.log_text.configure(state="disabled")

        tabla_frame = ctk.CTkFrame(right, fg_color=COLORES["panel"], corner_radius=12)
        tabla_frame.grid(row=1, column=0, sticky="nsew")
        tabla_frame.rowconfigure(1, weight=1)
        tabla_frame.columnconfigure(0, weight=1)
        ctk.CTkLabel(tabla_frame, text="Resultados", font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=COLORES["muted"]).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 6))

        style = ttv.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview", background=COLORES["card"], foreground=COLORES["text"],
                        fieldbackground=COLORES["card"], rowheight=28, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Dark.Treeview.Heading", background=COLORES["panel"], foreground=COLORES["muted"],
                        relief="flat", font=("Segoe UI", 10, "bold"))
        style.map("Dark.Treeview", background=[("selected", COLORES["accent"])], foreground=[("selected", "white")])
        style.map("Dark.Treeview.Heading", background=[("active", COLORES["border"])])

        cols = ("Cadena", "SKU", "Producto", "Precio_Normal", "Precio_Promo", "En_Stock")
        tree_container = tk.Frame(tabla_frame, bg=COLORES["card"])
        tree_container.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        tabla_frame.rowconfigure(1, weight=1)
        tabla_frame.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        self.tabla = ttv.Treeview(tree_container, columns=cols, show="headings", style="Dark.Treeview")
        widths = {"Cadena": 110, "SKU": 130, "Producto": 240, "Precio_Normal": 110, "Precio_Promo": 110, "En_Stock": 70}
        for col in cols:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=widths[col], anchor="center")

        vsb = ttv.Scrollbar(tree_container, orient="vertical", command=self.tabla.yview)
        hsb = ttv.Scrollbar(tree_container, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.tabla.tag_configure("odd", background="#1e2235")
        self.tabla.tag_configure("even", background=COLORES["card"])

    def _on_cadena_change(self, value=None):
        if self.cadena_var.get() == "Cruz Verde":
            self.cookie_frame.pack(padx=16, pady=(0, 10), after=self.cadena_menu)
        else:
            self.cookie_frame.pack_forget()

    def _log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.update_idletasks()

    def _set_status(self, msg, color=None):
        self.status_var.set(msg)
        if color:
            self.status_lbl.configure(text_color=color)

    def _cargar_archivo(self):
        path = filedialog.askopenfilename(filetypes=[("Excel/CSV", "*.xlsx *.csv")])
        if not path:
            return
        try:
            df = pd.read_csv(path) if path.endswith(".csv") else pd.read_excel(path)
            cadena_actual = self.cadena_var.get()
            if "SKU" in df.columns and "Cadena" in df.columns:
                skus = df[df["Cadena"].str.lower() == cadena_actual.lower()]["SKU"].astype(str).tolist()
            elif "SKU" in df.columns:
                skus = df["SKU"].astype(str).tolist()
            else:
                messagebox.showerror("Error", "El archivo debe tener una columna 'SKU'")
                return
            self.sku_text.delete("1.0", "end")
            self.sku_text.insert("1.0", "\n".join(skus))
            self.archivo_label.configure(text=f"✅ {len(skus)} SKUs cargados")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")

    def _iniciar(self):
        skus_raw = self.sku_text.get("1.0", "end").strip()
        if not skus_raw:
            messagebox.showwarning("Atención", "Ingresa al menos un SKU")
            return
        skus = [s.strip() for s in skus_raw.splitlines() if s.strip()]
        cadena = self.cadena_var.get()
        if cadena == "Cruz Verde" and not self.connect_sid_var.get().strip():
            messagebox.showerror("Error", "Cruz Verde requiere la cookie connect.sid")
            return
        self.btn_iniciar.configure(state="disabled", text="⏳  Extrayendo...")
        self.btn_csv.configure(state="disabled")
        self.btn_xlsx.configure(state="disabled")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        self._set_status(f"Extrayendo {len(skus)} SKUs de {cadena}…", COLORES["warning"])

        def run():
            self._log(f"🚀 Iniciando — {cadena} — {len(skus)} SKUs")
            self._log("─" * 55)
            try:
                df = self._dispatch(cadena, skus)
                self.df_resultado = df
                self._poblar_tabla(df)
                if df is not None and not df.empty:
                    self._log("─" * 55)
                    self._log(f"✅ Completado — {len(df)} productos")
                    self.btn_csv.configure(state="normal")
                    self.btn_xlsx.configure(state="normal")
                    self._set_status(f"✅ {len(df)} productos extraídos de {cadena}", COLORES["success"])
                else:
                    self._log("⚠️ Sin resultados")
                    self._set_status("⚠️ Sin resultados", COLORES["warning"])
            except Exception as e:
                self._log(f"❌ Error general: {e}")
                self._set_status(f"❌ Error: {e}", COLORES["danger"])
            self.btn_iniciar.configure(state="normal", text="🚀  Iniciar extraccion")

        threading.Thread(target=run, daemon=True).start()

    def _iniciar_base(self):
        file_path = "skus_base.xlsx"
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"No se encontro '{file_path}' en la carpeta del programa.")
            return
        try:
            df_base = pd.read_excel(file_path)
            if "SKU" not in df_base.columns or "Cadena" not in df_base.columns:
                messagebox.showerror("Error", "El Excel debe tener columnas 'SKU' y 'Cadena'.")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer el archivo:\n{e}")
            return

        cadenas_presentes = df_base["Cadena"].astype(str).str.lower().unique()
        cookie_cv = self.connect_sid_var.get().strip()
        if any("cruz verde" in c for c in cadenas_presentes) and not cookie_cv:
            if not messagebox.askyesno("Falta Cookie", "Hay SKUs de Cruz Verde pero no hay cookie.\n¿Continuar omitiendo Cruz Verde?"):
                return

        self.btn_iniciar.configure(state="disabled")
        self.btn_base.configure(state="disabled", text="⏳  Procesando Base…")
        self.btn_csv.configure(state="disabled")
        self.btn_xlsx.configure(state="disabled")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        self._set_status(f"Procesando base con {len(df_base)} registros…", COLORES["warning"])

        def run_base():
            self._log(f"⚡ Extraccion MASIVA desde {file_path}")
            self._log("─" * 55)
            all_dfs = []
            for cadena, group in df_base.groupby("Cadena"):
                skus = group["SKU"].dropna().astype(str).str.strip().tolist()
                cadena_lower = str(cadena).lower().strip()
                self._log(f"\n▶ {cadena} — {len(skus)} SKUs")
                try:
                    if "cruz verde" in cadena_lower and not cookie_cv:
                        df_res = pd.DataFrame()
                    else:
                        df_res = self._dispatch(cadena_lower, skus, cookie_cv)
                    if df_res is not None and not df_res.empty:
                        all_dfs.append(df_res)
                except Exception as e:
                    self._log(f"❌ Error critico en {cadena}: {e}")

            if all_dfs:
                self.df_resultado = pd.concat(all_dfs, ignore_index=True)
                self._poblar_tabla(self.df_resultado)
                self._log(f"\n{'─'*55}")
                self._log(f"✅ BASE COMPLETADA — {len(self.df_resultado)} productos")
                self._set_status(f"✅ Base procesada: {len(self.df_resultado)} productos", COLORES["success"])
                self.btn_csv.configure(state="normal")
                self.btn_xlsx.configure(state="normal")
            else:
                self._log("⚠️ Sin resultados")
                self._set_status("⚠️ Sin resultados", COLORES["warning"])

            self.btn_iniciar.configure(state="normal")
            self.btn_base.configure(state="normal", text="⚡  Ejecutar skus_base.xlsx")

        threading.Thread(target=run_base, daemon=True).start()

    def _dispatch(self, cadena, skus, cookie_cv=None):
        c = str(cadena).lower()
        if "ahumada" in c:
            return scrape_ahumada(skus, self._log)
        elif "cruz verde" in c:
            return scrape_cruzverde(skus, cookie_cv or self.connect_sid_var.get().strip(), self._log)
        elif "jumbo" in c:
            return scrape_jumbo(skus, self._log)
        elif "preunic" in c:
            return scrape_preunic(skus, self._log)
        elif "salcobrand" in c:
            return scrape_salcobrand(skus, self._log)
        elif "santa isabel" in c:
            return scrape_santaisabel(skus, self._log)
        elif "tottus" in c:
            return scrape_tottus(skus, self._log)
        elif "unimarc" in c:
            return scrape_unimarc(skus, self._log)
        elif "walmart" in c or "lider" in c:
            return scrape_walmart(skus, self._log)
        else:
            self._log(f"⚠️ Cadena no reconocida: '{cadena}'")
            return pd.DataFrame()

    def _poblar_tabla(self, df):
        if df is None or df.empty:
            return
        for i, (_, row) in enumerate(df.iterrows()):
            tag = "odd" if i % 2 else "even"
            promo = row.get('Precio_Promo')
            self.tabla.insert("", "end", tags=(tag,), values=(
                row.get("Cadena", ""), row.get("SKU", ""),
                str(row.get("Producto", ""))[:55],
                f"${row.get('Precio_Normal', 0):,}",
                f"${int(promo):,}" if pd.notna(promo) and promo else "—",
                "✅" if row.get("En_Stock") else "❌"
            ))

    def _exportar(self):
        if self.df_resultado is None or self.df_resultado.empty:
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=f"precios_{ts}.csv",
                                            filetypes=[("CSV", "*.csv")])
        if path:
            self.df_resultado.to_csv(path, index=False, encoding="utf-8-sig")
            messagebox.showinfo("✅ Exportado", f"Guardado en:\n{path}")

    def _exportar_xlsx(self):
        if self.df_resultado is None or self.df_resultado.empty:
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"precios_{ts}.xlsx",
                                            filetypes=[("Excel", "*.xlsx")])
        if path:
            self.df_resultado.to_excel(path, index=False)
            messagebox.showinfo("✅ Exportado", f"Guardado en:\n{path}")


if __name__ == "__main__":
    app = App()
    app.mainloop()

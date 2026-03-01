import requests
import pandas as pd
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def obtener_tokens_unimarc():
    """Abre el navegador una sola vez para obtener los tokens de sesión."""
    print("🔄 Obteniendo tokens de sesión...")

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # No abre ventana visible
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get("https://www.unimarc.cl")
        time.sleep(4)

        cookies = {c['name']: c['value'] for c in driver.get_cookies()}
        anonymous = cookies.get('sessionAnonymousId', '')
        session = cookies.get('sessionNanoId', '')

        if anonymous and session:
            print(f"✅ Tokens obtenidos correctamente.")
        else:
            print("⚠️ No se pudieron obtener los tokens, revisa el sitio.")

        return anonymous, session

    finally:
        driver.quit()


def limpiar_precio(precio_str):
    if not precio_str:
        return 0
    return int(re.sub(r'[^\d]', '', precio_str))


def extraer_precios_unimarc(ref_ids):
    anonymous, session = obtener_tokens_unimarc()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://www.unimarc.cl",
        "Referer": "https://www.unimarc.cl/",
        "channel": "UNIMARC",
        "source": "web",
        "version": "1.0.0",
        "anonymous": anonymous,
        "session": session,
    }

    print(f"\n--- Extrayendo precios desde Unimarc ({len(ref_ids)} SKUs) ---")
    resultados = []

    for ref_id in ref_ids:
        print(f"Procesando refId: {ref_id}...")

        url = "https://bff-unimarc-ecommerce.unimarc.cl/catalog/product/search"
        body = {
            "from": "0",
            "orderBy": "",
            "searching": ref_id.lower(),
            "promotionsOnly": False,
            "to": "49",
            "userTriggered": True
        }

        try:
            respuesta = requests.post(
                url, headers=headers, json=body, timeout=10)

            if respuesta.status_code == 200:
                datos = respuesta.json()
                productos = datos.get('availableProducts', [])

                if productos:
                    producto = None
                    for p in productos:
                        if p.get('item', {}).get('refId', '').upper() == ref_id.upper():
                            producto = p
                            break
                    if not producto:
                        producto = productos[0]

                    item = producto.get('item', {})
                    price = producto.get('price', {})

                    nombre = item.get('nameComplete', 'Sin nombre')
                    sku = item.get('sku', ref_id)
                    en_oferta = price.get('inOffer', False)

                    precio_normal = limpiar_precio(price.get('listPrice', '0'))
                    precio_oferta = limpiar_precio(price.get('price', '0'))
                    precio_promo_final = precio_oferta if en_oferta and precio_oferta < precio_normal else None

                    resultados.append({
                        "Cadena": "Unimarc",
                        "Ref_ID": ref_id,
                        "SKU": sku,
                        "Producto": nombre,
                        "Precio_Normal": precio_normal,
                        "Precio_Promo": precio_promo_final,
                        "En_Stock": price.get('availableQuantity', 0) > 0,
                    })
                else:
                    print(f"⚠️ refId {ref_id} no encontrado en el catálogo.")
            else:
                print(f"❌ Error {respuesta.status_code} con refId {ref_id}")

        except Exception as e:
            print(f"❌ Error de conexión con refId {ref_id}: {e}")

        time.sleep(1.5)

    if resultados:
        df = pd.DataFrame(resultados)
        print("\n✅ ¡Extracción completada con éxito!\n")
        print(df.to_string(index=False))
        return df
    else:
        return None


ref_ids_prueba = [
    "000000000000650823-UN",
    "000000000000324538-UN"
]
df_unimarc = extraer_precios_unimarc(ref_ids_prueba)

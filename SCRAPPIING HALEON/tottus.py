import pandas as pd
import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


def extraer_precios_tottus(codigos):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationDetection")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager().install()), options=chrome_options)

    print("--- Extrayendo precios desde Tottus ---")
    resultados = []

    for codigo in codigos:
        print(f"Procesando código: {codigo}...")
        url = f"https://www.tottus.cl/tottus-cl/buscar?Ntt={codigo}"

        try:
            driver.get(url)

            # Esperamos que cargue el JSON-LD del producto
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "script[type='application/ld+json']"))
            )
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Buscamos todos los bloques JSON-LD
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

                # Extraemos todos los precios disponibles
                precios = sorted([int(o.get("price", 0))
                                 for o in offers if o.get("price")])

                precio_normal = max(precios) if precios else 0
                precio_promo = min(precios) if len(precios) > 1 else None

                # Verificamos stock
                en_stock = any(
                    "InStock" in o.get("availability", "") for o in offers
                )

                resultados.append({
                    "Cadena": "Tottus",
                    "Codigo": codigo,
                    "Producto": nombre,
                    "Precio_Normal": precio_normal,
                    "Precio_Promo": precio_promo,
                    "En_Stock": en_stock,
                })
            else:
                print(f"⚠️ Código {codigo} no encontrado.")

        except Exception as e:
            print(f"❌ Error con código {codigo}: {e}")

        time.sleep(2)

    driver.quit()

    if resultados:
        df = pd.DataFrame(resultados)
        print("\n✅ ¡Extracción completada con éxito!\n")
        print(df.to_string(index=False))
        return df
    else:
        return None


codigos_prueba = [
    "20547253",
    "20388449"
]
df_tottus = extraer_precios_tottus(codigos_prueba)

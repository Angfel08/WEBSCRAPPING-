import requests
import pandas as pd
import time
import json
from bs4 import BeautifulSoup


def extraer_precios_ahumada(codigos):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9",
        "Referer": "https://www.farmaciasahumada.cl/"
    }

    print("--- Extrayendo precios desde Farmacias Ahumada ---")
    resultados = []

    for codigo in codigos:
        print(f"Procesando código: {codigo}...")
        url = f"https://www.farmaciasahumada.cl/{codigo}.html"

        try:
            respuesta = requests.get(url, headers=headers, timeout=10)

            if respuesta.status_code == 200:
                soup = BeautifulSoup(respuesta.text, "html.parser")

                # --- Precio desde JSON-LD (precio oferta o precio único) ---
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

                    # --- Precio normal desde el HTML (etiqueta <del>) ---
                    precio_normal = None
                    strike = soup.find("span", class_="strike-through")
                    if strike:
                        value_span = strike.find("span", class_="value")
                        if value_span and value_span.get("content"):
                            precio_normal = int(float(value_span["content"]))

                    # Si hay precio tachado, el JSON-LD tiene el precio promo
                    # Si no hay precio tachado, el JSON-LD tiene el precio normal
                    if precio_normal:
                        precio_promo_final = precio_jsonld if precio_jsonld < precio_normal else None
                    else:
                        precio_normal = precio_jsonld
                        precio_promo_final = None

                    resultados.append({
                        "Cadena": "Ahumada",
                        "Codigo": codigo,
                        "Producto": nombre,
                        "Precio_Normal": precio_normal,
                        "Precio_Promo": precio_promo_final,
                        "En_Stock": en_stock,
                    })
                else:
                    print(f"⚠️ Código {codigo} no encontrado.")
            else:
                print(f"❌ Error {respuesta.status_code} con código {codigo}")

        except Exception as e:
            print(f"❌ Error de conexión con código {codigo}: {e}")

        time.sleep(1.5)

    if resultados:
        df = pd.DataFrame(resultados)
        print("\n✅ ¡Extracción completada con éxito!\n")
        print(df.to_string(index=False))
        return df
    else:
        return None


codigos_prueba = [
    "72820",
    "90926",
    "91670"
]
df_ahumada = extraer_precios_ahumada(codigos_prueba)

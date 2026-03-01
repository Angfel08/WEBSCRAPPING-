import requests
import pandas as pd
import time
import json


def extraer_precios_preunic(skus):
    url = "https://7gdqzike3q-dsn.algolia.net/1/indexes/*/queries"
    params = {
        "x-algolia-agent": "Algolia for JavaScript (4.24.0); Browser (lite); instantsearch.js (4.74.0); react (18.3.1); react-instantsearch (7.13.0); react-instantsearch-core (7.13.0); next.js (14.2.32); JS Helper (3.22.4)",
        "x-algolia-api-key": "dcb263ac3f5bb5b523aad2f8c6029f7f",
        "x-algolia-application-id": "7GDQZIKE3Q"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://preunic.cl",
        "Referer": "https://preunic.cl/"
    }

    print("--- Extrayendo precios desde Preunic ---")
    resultados = []

    for sku in skus:
        print(f"Procesando SKU: {sku}...")

        body = json.dumps({
            "requests": [{
                "indexName": "Ecommerce-Products_production",
                "params": f"clickAnalytics=true&facets=%5B%22brand%22%2C%22categories.lvl0%22%2C%22has_promotions%22%2C%22has_sb_promotions%22%5D&filters=(communes%3A%22340%22%20OR%20zones%3A%2239%22%20OR%20store_exclusive%3Afalse)%20AND%20state%3Aactive&hitsPerPage=24&page=0&query={sku}"
            }]
        })

        try:
            respuesta = requests.post(
                url, headers=headers, params=params, data=body, timeout=10)

            if respuesta.status_code == 200:
                datos = respuesta.json()
                hits = datos.get('results', [{}])[0].get('hits', [])

                # Buscamos match exacto por SKU
                producto = None
                for h in hits:
                    if str(h.get('sku')) == str(sku):
                        producto = h
                        break
                if not producto and hits:
                    producto = hits[0]

                if producto:
                    nombre = producto.get('name', 'Sin nombre')
                    precio_normal = producto.get('price', 0)
                    precio_oferta = producto.get('offer_price', 0)
                    precio_tarjeta = producto.get('card_price', 0)

                    # Precio promo: tomamos el mejor precio disponible
                    precio_promo_final = None
                    if precio_oferta and precio_oferta < precio_normal:
                        precio_promo_final = precio_oferta
                    if precio_tarjeta and precio_tarjeta < precio_normal:
                        precio_promo_final = precio_tarjeta  # tarjeta suele ser el más bajo

                    resultados.append({
                        "Cadena": "Preunic",
                        "SKU": sku,
                        "Producto": nombre,
                        "Precio_Normal": precio_normal,
                        "Precio_Oferta": precio_oferta if precio_oferta < precio_normal else None,
                        "Precio_Tarjeta": precio_tarjeta if precio_tarjeta < precio_normal else None,
                        "En_Stock": producto.get('state') == 'active',
                    })
                else:
                    print(f"⚠️ SKU {sku} no encontrado en el catálogo.")
            else:
                print(f"❌ Error {respuesta.status_code} con SKU {sku}")

        except Exception as e:
            print(f"❌ Error de conexión con SKU {sku}: {e}")

        time.sleep(1.5)

    if resultados:
        df = pd.DataFrame(resultados)
        print("\n✅ ¡Extracción completada con éxito!\n")
        print(df.to_string(index=False))
        return df
    else:
        return None


skus_prueba = [
    "584056",
    "584742"
]
df_preunic = extraer_precios_preunic(skus_prueba)

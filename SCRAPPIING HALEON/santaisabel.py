import requests
import pandas as pd
import time


def extraer_precios_santaisabel(skus):
    # La API maestra y tu Pase VIP
    url = "https://be-reg-groceries-bff-sisa.ecomm.cencosud.com/catalog/plp"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "ApiKey": "be-reg-groceries-sisa-catalog-wdhhq5a2fken"
    }

    print("--- 🎯 Extracción Definitiva: SANTA ISABEL (API BFF) ---")
    resultados = []

    for sku in skus:
        print(f"\nBuscando SKU: {sku}...")

        payload = {
            "store": "pedrofontova",  # Puedes cambiar esto por el ID de cualquier otro local
            "collections": [],
            "fullText": sku,
            "hideUnavailableItems": False,  # Nos muestra el producto aunque esté agotado
            "brands": [],
            "from": 0,
            "to": 40,
            "orderBy": "",
            "promotionalCards": False,
            "selectedFacets": [],
            "sponsoredProducts": True
        }

        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)

            if res.status_code == 200:
                datos = res.json()
                productos = datos.get('products', [])

                if productos:
                    # Entramos a la carpeta 'items' que acabas de descubrir
                    items = productos[0].get('items', [])

                    if items:
                        item = items[0]
                        nombre = item.get('name', 'Sin nombre')
                        precio_normal = item.get('listPrice', 0)
                        precio_oferta = item.get('price', 0)
                        en_stock = item.get('stock', False)

                        # Calculamos si hay promoción real
                        precio_promo_final = precio_oferta if precio_oferta < precio_normal else None

                        resultados.append({
                            "Cadena": "Santa Isabel",
                            "SKU": sku,
                            "Producto": nombre,
                            "Precio_Normal": precio_normal,
                            "Precio_Promo": precio_promo_final,
                            "En_Stock": en_stock
                        })

                        estado = "✅ En Stock" if en_stock else "⚠️ Agotado"
                        print(
                            f"  {estado} | {nombre} | Normal: ${precio_normal}")
                    else:
                        print(
                            f"  ⚠️ El SKU {sku} existe, pero no tiene datos de precio/stock.")
                else:
                    print(f"  ❌ SKU {sku} no encontrado en la base maestra.")
            else:
                print(f"  ❌ Error HTTP {res.status_code}")

        except Exception as e:
            print(f"  ❌ Error de conexión: {e}")

        time.sleep(1)  # Pausa de cortesía

    # Retornamos el DataFrame limpio
    if resultados:
        df = pd.DataFrame(resultados)
        return df
    else:
        return pd.DataFrame()


# Los SKUs de la categoría
mis_skus = ["996166", "2006539", "1672590"]

# Ejecución
df_si = extraer_precios_santaisabel(mis_skus)

print("\n--- REPORTE FINAL SANTA ISABEL ---")
if not df_si.empty:
    print(df_si.to_string(index=False))

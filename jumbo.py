import requests
import pandas as pd
import time


def extraer_precios_jumbo(skus):
    api_key = "key_JopvNXKS61kwGkBe"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }

    print("--- Extrayendo precios desde Jumbo (Tienda Web Principal) ---")
    resultados = []

    for sku in skus:
        print(f"Procesando SKU: {sku}...")
        url = f"https://pwcdauseo-zone.cnstrc.com/search/{sku}"
        params = {"key": api_key, "c": "ciojs-2.1368.5"}

        try:
            respuesta = requests.get(
                url, headers=headers, params=params, timeout=10)

            if respuesta.status_code == 200:
                datos = respuesta.json()
                lista_resultados = datos.get('response', {}).get('results', [])

                if lista_resultados:
                    producto_raiz = lista_resultados[0]
                    nombre = producto_raiz.get('value', 'Sin nombre')

                    # Entramos a la lista de variaciones (los distintos locales)
                    variaciones = producto_raiz.get('variations', [])

                    precio_normal = 0
                    precio_oferta = 0
                    en_stock = False
                    tienda_encontrada = "No definida"

                    # Buscamos la tienda "jumbocl" (el precio web estándar)
                    for var in variaciones:
                        data_local = var.get('data', {})
                        if data_local.get('storeId') == 'jumbocl':
                            precio_normal = data_local.get('listPrice', 0)
                            precio_oferta = data_local.get('sellingPrice', 0)
                            en_stock = not data_local.get('outOfStock', True)
                            tienda_encontrada = "jumbocl"
                            break  # Encontramos la tienda, detenemos la búsqueda

                    # Si por alguna razón este SKU no está en 'jumbocl', tomamos el primero como respaldo
                    if tienda_encontrada == "No definida" and variaciones:
                        fallback_data = variaciones[0].get('data', {})
                        precio_normal = fallback_data.get('listPrice', 0)
                        precio_oferta = fallback_data.get('sellingPrice', 0)
                        en_stock = not fallback_data.get('outOfStock', True)
                        tienda_encontrada = fallback_data.get(
                            'storeId', 'Desconocida')

                    precio_promo_final = precio_oferta if precio_oferta < precio_normal else None

                    resultados.append({
                        "Cadena": "Jumbo",
                        "SKU": sku,
                        "Producto": nombre,
                        "Precio_Normal": precio_normal,
                        "Precio_Promo": precio_promo_final,
                        "En_Stock": en_stock,
                        "Store_ID": tienda_encontrada
                    })
                else:
                    print(f"⚠️ SKU {sku} no encontrado en el catálogo.")
            else:
                print(f"❌ Error {respuesta.status_code} con el SKU {sku}")

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


skus_prueba = ["1933911", "1353774", "996166"]
df_jumbo = extraer_precios_jumbo(skus_prueba)

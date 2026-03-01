import requests
import pandas as pd
import time

# Cambiar manualmente la cookie connect.sid, CONTROL F12, luegoo applicattion, luego cookies, la primera
# y buscar connect.sid, pegarla abajo


def obtener_cookies_cruzverde():
    print("✅ Usando cookie de sesión manual.")
    return {
        "connect.sid": "s%3Acruzverde-829bd6dc-09fb-4189-8e03-1effae43b4ac.%2ByacJT1HYy5%2B%2FdNKTaKfhthinHTUOQ3if4yeJTC9WyY"
    }


def extraer_precios_cruzverde(codigos):
    cookies = obtener_cookies_cruzverde()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.cruzverde.cl",
        "Referer": "https://www.cruzverde.cl/"
    }

    print("\n--- Extrayendo precios desde Cruz Verde ---")
    resultados = []

    for codigo in codigos:
        print(f"Procesando código: {codigo}...")
        url = f"https://api.cruzverde.cl/product-service/products/detail/{codigo}"
        params = {"inventoryId": "Zonapañales1119"}

        try:
            respuesta = requests.get(
                url, headers=headers, params=params, cookies=cookies, timeout=10)

            if respuesta.status_code == 200:
                datos = respuesta.json()
                producto = datos.get("productData", {})

                if producto:
                    nombre = producto.get("name", "Sin nombre")
                    prices = producto.get("prices", {})
                    stock = producto.get("stock", 0)

                    precio_normal = prices.get("price-list-cl", 0)
                    precio_oferta = prices.get("price-sale-cl", 0)
                    precio_promo_final = precio_oferta if precio_oferta and precio_oferta < precio_normal else None

                    resultados.append({
                        "Cadena": "Cruz Verde",
                        "Codigo": codigo,
                        "Producto": nombre,
                        "Precio_Normal": precio_normal,
                        "Precio_Promo": precio_promo_final,
                        "En_Stock": stock > 0,
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
    "579721",
    "288095",
    "290664"
]
df_cruzverde = extraer_precios_cruzverde(codigos_prueba)

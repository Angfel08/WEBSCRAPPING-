import asyncio
from playwright.async_api import async_playwright
import pandas as pd


async def extraer_salcobrand_retail_rocket(skus):
    print("--- Iniciando Captura via Retail Rocket para SALCOBRAND ---")
    resultados = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Validamos sesión en la página principal primero
        print("Sincronizando con Salcobrand...")
        await page.goto("https://salcobrand.cl/", wait_until="networkidle")
        await asyncio.sleep(2)

        for sku in skus:
            print(f"Consultando SKU: {sku}...")

            # Construimos la URL de la API de Retail Rocket que encontraste
            api_url = f"https://api.retailrocket.net/api/1.0/partner/602bba6097a5281b4cc438c9/items/?itemsIds={sku}&format=json"

            try:
                # Ejecutamos la consulta desde el contexto del navegador
                respuesta = await page.evaluate(f"fetch('{api_url}').then(res => res.json())")

                if respuesta and len(respuesta) > 0:
                    item = respuesta[0]  # Retail Rocket devuelve una lista

                    nombre = item.get('Name', 'No encontrado')
                    precio_actual = item.get('Price', 0)
                    precio_viejo = item.get('OldPrice', 0)

                    # Determinamos el precio normal y la oferta
                    # Si OldPrice es 0, el precio normal es el actual
                    p_normal = precio_viejo if precio_viejo > 0 else precio_actual
                    p_promo = precio_actual if precio_viejo > 0 else None

                    resultados.append({
                        "Cadena": "Salcobrand",
                        "SKU": sku,
                        "Producto": nombre,
                        "Precio_Normal": p_normal,
                        "Precio_Promo": p_promo,
                        "Stock": item.get('IsAvailable', False)
                    })
                    print(f"✅ {nombre}: ${p_normal}")
                else:
                    print(f"⚠️ El SKU {sku} no devolvió datos en la API.")

            except Exception as e:
                print(f"❌ Error en SKU {sku}: {e}")

            await asyncio.sleep(1)

        await browser.close()

    return pd.DataFrame(resultados)

# Tus SKUs de prueba
mis_skus_sb = ["592919", "577719", "575368"]

if __name__ == "__main__":
    df_sb = asyncio.run(extraer_salcobrand_retail_rocket(mis_skus_sb))
    print("\n--- REPORTE FINAL SALCOBRAND ---")
    print(df_sb)

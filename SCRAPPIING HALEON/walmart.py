import asyncio
import json
from playwright.async_api import async_playwright
import pandas as pd


async def extraer_lider_final_perfecto(skus):
    print("--- 🔬 LIDER: Extracción de Nombre Exacto y Desglose de Precios ---")
    resultados = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        for sku in skus:
            print(f"\nAnalizando SKU: {sku}...")
            url = f"https://super.lider.cl/ip/{sku}"

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(3000)

                # Extraemos el JSON oculto
                json_raw = await page.evaluate('document.getElementById("__NEXT_DATA__").innerText')
                data = json.loads(json_raw)

                # Ruta maestra que encontraste:
                # props -> pageProps -> initialData -> data -> product
                base_product = data['props']['pageProps']['initialData']['data']['product']

                # --- CAPTURA DEL NOMBRE ---
                # Usamos la ruta exacta que encontraste: .get('name')
                nombre = base_product.get('name', 'Producto sin nombre')

                # --- CAPTURA DE PRECIOS (De tu imagen) ---
                price_info = base_product.get('priceInfo', {})

                # currentPrice (el precio de oferta o actual en tu imagen)
                p_actual = price_info.get('currentPrice', {}).get('price', 0)

                # wasPrice (el precio normal/tachado en tu imagen)
                p_anterior = price_info.get('wasPrice', {}).get('price', 0)

                # Lógica para definir Normal vs Oferta
                if p_anterior and p_anterior > 0:
                    precio_normal = p_anterior
                    precio_oferta = p_actual
                else:
                    precio_normal = p_actual
                    precio_oferta = None

                resultados.append({
                    "Cadena": "Lider",
                    "SKU": sku,
                    "Producto": nombre,
                    "Precio_Normal": precio_normal,
                    "Precio_Oferta": precio_oferta,
                    "Disponible": base_product.get('inventory', {}).get('isAvailable', False)
                })

                print(f"✅ ¡Capturado!: {nombre}")
                print(
                    f"   Normal: ${precio_normal} | Oferta: ${precio_oferta if precio_oferta else 'Sin descuento'}")

            except Exception as e:
                print(f"❌ Error en la ruta del JSON: {str(e)[:100]}")

        await browser.close()

    return pd.DataFrame(resultados)

# Tu SKU de prueba (Sensodyne Extra Fresh 90g)
mis_skus = ["00779464017072", "00779464017242"]

if __name__ == "__main__":
    df_lider = asyncio.run(extraer_lider_final_perfecto(mis_skus))
    print("\n" + "="*50)
    print("REPORTE LIDER: DATOS ESTRUCTURADOS")
    print("="*50)
    print(df_lider[['Producto', 'Precio_Normal', 'Precio_Oferta']])

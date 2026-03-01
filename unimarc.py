import asyncio
import json
import pandas as pd
import re
from playwright.async_api import async_playwright


def limpiar_precio(texto_precio):
    """Extrae solo los números de strings como '$4.000'"""
    if not texto_precio:
        return 0
    solo_numeros = re.sub(r'[^\d]', '', str(texto_precio))
    return int(solo_numeros) if solo_numeros else 0


async def extraer_unimarc_anti_403(skus):
    print("--- 🛡️ UNIMARC: Extracción Anti-Bloqueo (BFF + Playwright) ---")
    resultados = []

    async with async_playwright() as p:
        # Usamos un navegador real para evitar el 403
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for sku in skus:
            # Limpieza de SKU: Unimarc prefiere solo el número (ej: 650823)
            sku_clean = re.sub(r'[^\d]', '', sku).lstrip('0')
            print(f"Consultando SKU: {sku_clean}...")

            # URL del BFF que encontraste
            url_api = f"https://bff-unimarc-ecommerce.unimarc.cl/catalog/product/search?id={sku_clean}"

            try:
                # Navegamos directamente a la API
                await page.goto(url_api, wait_until="networkidle", timeout=30000)

                # Obtenemos el contenido de la página (que es un JSON)
                content = await page.evaluate("() => document.body.innerText")
                data = json.loads(content)

                # Usamos la estructura que me pasaste en el F12
                productos = data.get('availableProducts', [])

                if productos:
                    prod = productos[0]
                    nombre = prod.get('name', 'Producto sin nombre')
                    price_data = prod.get('price', {})

                    p_actual = limpiar_precio(price_data.get('price'))
                    p_normal = limpiar_precio(price_data.get('listPrice'))

                    resultados.append({
                        "Cadena": "Unimarc",
                        "SKU": sku_clean,
                        "Producto": nombre,
                        "Precio_Normal": p_normal if p_normal > p_actual else p_actual,
                        "Precio_Oferta": p_actual if p_actual < p_normal else None,
                        "Disponible": True
                    })
                    print(f"✅ Capturado: {nombre} | ${p_actual}")
                else:
                    print(
                        f"⚠️ SKU {sku_clean} no aparece en 'availableProducts'.")

            except Exception as e:
                print(f"❌ Error en SKU {sku_clean}: {str(e)[:50]}")

        await browser.close()

    return pd.DataFrame(resultados)

# Tu SKU de prueba (Limpiamos los ceros a la izquierda y el -un)
mis_skus = ["000000000000650823-un"]

if __name__ == "__main__":
    df = asyncio.run(extraer_unimarc_anti_403(mis_skus))
    print("\n" + "="*50)
    print("REPORTE UNIMARC (ANTI-403)")
    print("="*50)
    if not df.empty:
        print(df[['Producto', 'Precio_Normal', 'Precio_Oferta']])
    else:
        print("No se obtuvieron datos. Revisa el SKU en el navegador.")

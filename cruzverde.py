import asyncio
from playwright.async_api import async_playwright
import pandas as pd


async def extraer_cruzverde_robusto(skus):
    print("--- Iniciando Captura Robusta para Cruz Verde ---")
    resultados = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Usamos una huella digital de navegador moderno
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # 1. PASO DE CALENTAMIENTO: Visitamos la home para obtener cookies de humano
        print("Obteniendo permisos del servidor...")
        await page.goto("https://www.cruzverde.cl/", wait_until="networkidle")
        await asyncio.sleep(3)

        for sku in skus:
            print(f"Buscando SKU: {sku}...")
            # Usamos una URL de búsqueda que es más estable que el slug fijo
            url_referencia = f"https://www.cruzverde.cl/search?q={sku}"

            try:
                # Vamos a la página de búsqueda del producto
                await page.goto(url_referencia, wait_until="networkidle", timeout=45000)

                # Definimos la API con el ID de zona codificado (%C3%B1 es la 'ñ')
                api_url = f"https://api.cruzverde.cl/product-service/products/detail/{sku}?inventoryId=Zonapa%C3%B1ales1119"

                # Ejecutamos el fetch con manejo de errores interno
                respuesta_json = await page.evaluate(f"""
                    fetch('{api_url}')
                    .then(res => res.ok ? res.json() : null)
                    .catch(() => null)
                """)

                if respuesta_json and 'productData' in respuesta_json:
                    p_data = respuesta_json.get('productData', {})
                    nombre = p_data.get('name', 'Nombre no encontrado')
                    precios = p_data.get('prices', {})

                    p_normal = precios.get('price-list-cl', 0)
                    p_oferta = precios.get('price-sale-cl', 0)

                    resultados.append({
                        "Cadena": "Cruz Verde",
                        "SKU": sku,
                        "Producto": nombre,
                        "Precio_Normal": p_normal,
                        "Precio_Promo": p_oferta if (p_oferta > 0 and p_oferta < p_normal) else None
                    })
                    print(f"✅ Capturado: {nombre} - ${p_normal}")
                else:
                    print(
                        f"⚠️ No se obtuvieron datos para el SKU {sku}. Reintentando con otro método...")
                    # Aquí podrías añadir una lógica de reintento si fuera necesario

            except Exception as e:
                print(f"❌ Error al procesar SKU {sku}: {e}")

            await asyncio.sleep(3)

        await browser.close()

    return pd.DataFrame(resultados)

# Tu lista actualizada de SKUs para Haleon
mis_skus = ["579721", "268576", "288173"]

if __name__ == "__main__":
    df_final = asyncio.run(extraer_cruzverde_robusto(mis_skus))
    print("\n--- REPORTE FINAL ACTUALIZADO ---")
    print(df_final)

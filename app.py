import streamlit as st
import fitz
import io

# Configuración de la pestaña del navegador
st.set_page_config(page_title="Bicha' P. Order", page_icon="📝")

def procesar_pdf(file_input):
    # Leer el archivo desde la memoria de Streamlit
    doc = fitz.open(stream=file_input.read(), filetype="pdf")
    
    # --- PASO 1: LOCALIZAR COLUMNAS (PÁGINA 1) ---
    pag1 = doc[0]
    pos_precio = pag1.search_for("PRECIO UNITARIO")
    pos_subtotal = pag1.search_for("SUBTOTAL")
    
    if not (pos_precio and pos_subtotal):
        return None

    x0_p, x1_p = pos_precio[0].x0, pos_precio[0].x1
    x0_s, x1_s = pos_subtotal[0].x0, pos_subtotal[0].x1

    # --- PASO 2: PROCESAR TODAS LAS PÁGINAS ---
    for num_pagina, page in enumerate(doc):
        
        # A. Determinar límite inferior (Paginado o Texto Legal de Cierre)
        y_limite_inferior = page.rect.height - 40 
        
        # Buscar etiquetas de paginado
        for etiqueta in ["Página", "Pagina", "Pág", "Pag"]:
            pos_paginado = page.search_for(etiqueta)
            if pos_paginado:
                y_limite_inferior = pos_paginado[0].y0 - 5
                break 

        # Buscar frase de cierre para detener el dibujo
        pos_cierre = page.search_for("EL PROVEEDOR Y COTEMAR")
        if pos_cierre:
            y_limite_inferior = pos_cierre[0].y0 - 10

        # B. PROCESAMIENTO SEGÚN EL TIPO DE PÁGINA
        if num_pagina == 0:
            # Página 1: Empezar debajo de los encabezados
            y_inicio = pos_precio[0].y1 + 2
            if y_inicio < y_limite_inferior:
                page.draw_rect(fitz.Rect(x0_p - 5, y_inicio + 5, x1_p + 5, y_limite_inferior), color=(1,1,1), fill=(1,1,1), overlay=True)
                page.draw_rect(fitz.Rect(x0_s - 5, y_inicio + 5, x1_s + 5, y_limite_inferior), color=(1,1,1), fill=(1,1,1), overlay=True)
        else:
            # Página 2 en adelante: Buscar INCOTERM como ancla de inicio
            pos_incoterm = page.search_for("INCOTERM")
            if pos_incoterm:
                y_ancla_incoterm = pos_incoterm[0].y1
                
                # Obtener líneas vectoriales para identificar filas de materiales
                dibujos = page.get_drawings()
                lineas_y = []
                for dibujo in dibujos:
                    for item in dibujo["items"]:
                        if item[0] == "l": 
                            pnt_inicio, pnt_fin = item[1], item[2]
                            # Filtro: línea horizontal larga debajo de INCOTERM y sobre el límite de cierre
                            if abs(pnt_inicio.y - pnt_fin.y) < 1.0 and abs(pnt_fin.x - pnt_inicio.x) > 200:
                                if y_ancla_incoterm < pnt_inicio.y < y_limite_inferior:
                                    lineas_y.append(pnt_inicio.y)
                
                lineas_y = sorted(list(set(lineas_y)))
                
                for i in range(len(lineas_y)):
                    y_actual = lineas_y[i]
                    # Bloque termina en la siguiente línea o en el límite legal/paginado
                    y_bloqueo_fin = lineas_y[i+1] - 1 if i < len(lineas_y) - 1 else y_limite_inferior
                    
                    if y_actual < y_limite_inferior:
                        page.draw_rect(fitz.Rect(x0_p - 5, y_actual + 1.5, x1_p + 5, y_bloqueo_fin), color=(1,1,1), fill=(1,1,1), overlay=True)
                        page.draw_rect(fitz.Rect(x0_s - 5, y_actual + 1.5, x1_s + 5, y_bloqueo_fin), color=(1,1,1), fill=(1,1,1), overlay=True)

    # --- PASO 3: APLANADO Y RETORNO ---
    doc.bake() # Fusiona los cuadros blancos con el PDF
    return doc.tobytes()

# --- INTERFAZ DE USUARIO (STREAMLIT) ---
st.sidebar.image("https://user10751.na.imgto.link/public/20260510/tux11.avif", width=200)
st.sidebar.title("Instrucciones")
st.sidebar.info("""
1. Sube tus Órdenes de Compra (PDF).
2. El sistema detectará las columnas de costos y el área de firmas.
3. Se ocultarán los precios hasta encontrar la frase de cierre legal.
""")

st.title("📝 Bicha' P. Order")
st.subheader("(Versión 1.0)")

st.markdown("Carga los archivos para procesarlos")

uploaded_files = st.file_uploader("Arrastra aquí los archivos PDF", type="pdf", accept_multiple_files=True)

if uploaded_files:
    st.write("---")
    for uploaded_file in uploaded_files:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text(f"📄 {uploaded_file.name}")
        with col2:
            with st.spinner("Procesando..."):
                pdf_bytes = procesar_pdf(uploaded_file)
                if pdf_bytes:
                    st.download_button(
                        label="Descargar",
                        data=pdf_bytes,
                        file_name=f"ANON_{uploaded_file.name}",
                        mime="application/pdf",
                        key=uploaded_file.name
                    )
                else:
                    st.error("Encabezados no detectados")

st.markdown("---")
st.caption("Herramienta de optimización Tótec.")

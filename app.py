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

    # Variable de control para detener el proceso en hojas posteriores
    stop_drawing_total = False

    # --- PASO 2: PROCESAR TODAS LAS PÁGINAS ---
    for num_pagina, page in enumerate(doc):
        
        # Si ya se detectó la frase de cierre en una hoja previa, terminamos el ciclo
        if stop_drawing_total:
            break
            
        # A. Determinar límite inferior estándar (Paginado)
        y_limite_inferior = page.rect.height - 40 
        for etiqueta in ["Página", "Pagina", "Pág", "Pag"]:
            pos_paginado = page.search_for(etiqueta)
            if pos_paginado:
                y_limite_inferior = pos_paginado[0].y0 - 5
                break 

        # B. DETECTAR FRASE DE CIERRE LEGAL
        # Si aparece, actualizamos el límite de ESTA hoja y activamos el freno para las SIGUIENTES
        pos_cierre = page.search_for("EL PROVEEDOR Y COTEMAR")
        if pos_cierre:
            y_limite_inferior = pos_cierre[0].y0 - 10
            stop_drawing_total = True # Freno activado

        # C. DIBUJO DE CUADROS SEGÚN EL TIPO DE PÁGINA
        if num_pagina == 0:
            # Página 1: Inicio debajo de encabezados
            y_inicio = pos_precio[0].y1 + 2
            if y_inicio < y_limite_inferior:
                page.draw_rect(fitz.Rect(x0_p - 5, y_inicio + 5, x1_p + 5, y_limite_inferior), color=(1,1,1), fill=(1,1,1), overlay=True)
                page.draw_rect(fitz.Rect(x0_s - 5, y_inicio + 5, x1_s + 5, y_limite_inferior), color=(1,1,1), fill=(1,1,1), overlay=True)
        else:
            # Página 2+: Inicio debajo de INCOTERM
            pos_incoterm = page.search_for("INCOTERM")
            if pos_incoterm:
                y_ancla = pos_incoterm[0].y1
                dibujos = page.get_drawings()
                lineas_y = sorted(list(set([it[1].y for d in dibujos for it in d["items"] if it[0] == "l" and abs(it[1].y - it[2].y) < 1.0 and abs(it[2].x - it[1].x) > 200 and y_ancla < it[1].y < y_limite_inferior])))
                
                for i in range(len(lineas_y)):
                    y_act = lineas_y[i]
                    y_sig = lineas_y[i+1] - 1 if i < len(lineas_y) - 1 else y_limite_inferior
                    
                    if y_act < y_limite_inferior:
                        page.draw_rect(fitz.Rect(x0_p - 5, y_act + 1.5, x1_p + 5, y_sig), color=(1,1,1), fill=(1,1,1), overlay=True)
                        page.draw_rect(fitz.Rect(x0_s - 5, y_act + 1.5, x1_s + 5, y_sig), color=(1,1,1), fill=(1,1,1), overlay=True)

    # --- PASO 3: FINALIZAR ---
    doc.bake()
    return doc.tobytes()

# --- INTERFAZ STREAMLIT ---
st.sidebar.image("https://user10751.na.imgto.link/public/20260510/tux11.avif", width=200)
st.sidebar.title("Instrucciones")
st.sidebar.info("""
1. Sube tus PDFs de Órdenes de Compra.
2. El sistema ocultará costos de las Ordenes de Compra'.
3. Desplegará la opción de descarga y listo!.
""")

st.title("📝 Anonimizador de O.C. V2")
st.subheader("División DSCM - Cotemar")

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
                    st.error("Encabezados no hallados")

st.markdown("---")
st.caption("Herramienta de optimización 🄯 Tótec 2026.")

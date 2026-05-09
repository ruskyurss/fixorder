import streamlit as st
import fitz
import io

def procesar_pdf(file_input):
    # Leer el archivo desde la memoria
    doc = fitz.open(stream=file_input.read(), filetype="pdf")
    
    # Identificar columnas en Pág 1
    pag1 = doc[0]
    pos_precio = pag1.search_for("PRECIO UNITARIO")
    pos_subtotal = pag1.search_for("SUBTOTAL")
    
    if not (pos_precio and pos_subtotal):
        return None

    x0_p, x1_p = pos_precio[0].x0, pos_precio[0].x1
    x0_s, x1_s = pos_subtotal[0].x0, pos_subtotal[0].x1

    for num_pagina, page in enumerate(doc):
        y_limite_inferior = page.rect.height - 40
        for etiqueta in ["Página", "Pagina", "Pág", "Pag"]:
            pos_paginado = page.search_for(etiqueta)
            if pos_paginado:
                y_limite_inferior = pos_paginado[0].y0 - 5
                break 

        if num_pagina == 0:
            y_inicio = pos_precio[0].y1 + 2
            page.draw_rect(fitz.Rect(x0_p - 5, y_inicio + 5, x1_p + 5, y_limite_inferior), color=(1,1,1), fill=(1,1,1), overlay=True)
            page.draw_rect(fitz.Rect(x0_s - 5, y_inicio + 5, x1_s + 5, y_limite_inferior), color=(1,1,1), fill=(1,1,1), overlay=True)
        else:
            pos_incoterm = page.search_for("INCOTERM")
            if pos_incoterm:
                y_ancla_incoterm = pos_incoterm[0].y1
                dibujos = page.get_drawings()
                lineas_y = sorted(list(set([item[1].y for d in dibujos for item in d["items"] if item[0] == "l" and abs(item[1].y - item[2].y) < 1.0 and abs(item[2].x - item[1].x) > 200 and y_ancla_incoterm < item[1].y < y_limite_inferior])))
                
                for i in range(len(lineas_y)):
                    y_actual = lineas_y[i]
                    y_bloqueo_fin = lineas_y[i+1] - 1 if i < len(lineas_y) - 1 else y_limite_inferior
                    page.draw_rect(fitz.Rect(x0_p - 5, y_actual + 1.5, x1_p + 5, y_bloqueo_fin), color=(1,1,1), fill=(1,1,1), overlay=True)
                    page.draw_rect(fitz.Rect(x0_s - 5, y_actual + 1.5, x1_s + 5, y_bloqueo_fin), color=(1,1,1), fill=(1,1,1), overlay=True)

    doc.bake()
    return doc.tobytes()

# INTERFAZ STREAMLIT
st.title("🛡️ Anonimizador de Órdenes Cotemar")
st.write("Sube tus archivos PDF para ocultar Precios Unitarios y Subtotales automáticamente.")

uploaded_files = st.file_uploader("Elige archivos PDF", type="pdf", accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        with st.spinner(f"Procesando {uploaded_file.name}..."):
            pdf_output = procesar_pdf(uploaded_file)
            if pdf_output:
                st.download_button(
                    label=f"Descargar {uploaded_file.name} anonimizado",
                    data=pdf_output,
                    file_name=f"ANON_{uploaded_file.name}",
                    mime="application/pdf"
                )
            else:
                st.error(f"No se pudo procesar {uploaded_file.name}: Encabezados no encontrados.")

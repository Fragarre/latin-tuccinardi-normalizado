import streamlit as st
import pandas as pd
import zipfile
import shutil
import tempfile
from pathlib import Path
import subprocess
import os
from PIL import Image
import plotly.graph_objects as go
from scipy.stats import t

# === CONFIGURACION ===
base_dir = Path("C:/Users/fraga/projects/stamatatos_spi_normalizado")
data_dir = base_dir / "data"
tabla_dir = data_dir / "resultados" / "tablas"
fragmentos_dir = data_dir / "fragmentos"
script_path = base_dir / "analisis_spi_completo.py"

st.set_page_config(page_title="Análisis de Autoría SPI", layout="centered")
st.title("Análisis de Autoría mediante SPI Normalizado")

# === SIDEBAR ===
st.sidebar.header("Parámetros del Modelo")
st.sidebar.info("""
Recarga la aplicación para nuevos ficheros.
Pueden realizarse varias ejecuciones sobre los mismos textos, variando parámetros n y s y volviendo a 'Ejecutar Análisis'
""")
n = st.sidebar.selectbox("Selecciona longitud del n-grama (n)", [3, 4, 5, 6], index=2)
s_input = st.sidebar.text_input("Cantidad de n-gramas más frecuentes (s):", value="1000")

# Validación de s
s = s_input.strip()
if s.lower() == "none":
    s_arg = "none"
else:
    try:
        int(s)
        s_arg = s
    except ValueError:
        st.error("El valor de 's' debe ser un número o la palabra 'None'")
        st.stop()

# === SUBIDA DE ARCHIVOS ===
st.subheader("Sube los archivos para el análisis")
zip_file = st.file_uploader("Archivo .zip con textos conocidos", type=["zip"], key="zip")
txt_file = st.file_uploader("Archivo .txt con texto dudoso", type=["txt"], key="txt")

# Guardar archivos al cargarlos
if zip_file:
    known_path = data_dir / "textos_ciertos" / "Known.zip"
    known_path.parent.mkdir(parents=True, exist_ok=True)
    with open(known_path, "wb") as f:
        f.write(zip_file.read())

if txt_file:
    unknown_path = data_dir / "texto_dudoso" / "Unknown.txt"
    unknown_path.parent.mkdir(parents=True, exist_ok=True)
    with open(unknown_path, "wb") as f:
        f.write(txt_file.read())

run_analysis = st.button("Ejecutar análisis")

if run_analysis:
    modelo_tag = f"n{n}_L{s if s.lower() != 'none' else 'ALL'}"

    # Limpiar resultados anteriores de ese modelo
    for file in tabla_dir.glob(f"*{modelo_tag}*.csv"):
        file.unlink()

    with st.spinner("Ejecutando análisis..."):
        result = subprocess.run([
            "python", str(script_path), str(n), s_arg
        ], capture_output=True, text=True)

    # Mostrar salida y errores del script
    st.text("Salida estándar del script:")
    st.code(result.stdout)

    st.text("Errores (si los hay):")
    st.code(result.stderr)

    if result.returncode != 0:
        st.error("Error en la ejecución del script")
    else:
        st.success("Análisis completado correctamente")

        tabla_path = tabla_dir / f"tabla3_spi_normalizados_{modelo_tag}.csv"
        if tabla_path.exists():
            df_spi = pd.read_csv(tabla_path)
            z_values = df_spi["SPI_normalizado"].tolist()
            nombres = df_spi["Fragmento"].tolist()

            hover_texts = []
            for frag in nombres:
                frag_path = fragmentos_dir / f"{frag}.txt"
                if frag_path.exists():
                    texto = frag_path.read_text(encoding="utf-8")
                    palabras = " ".join(texto.split()[:20]) + "..."
                else:
                    palabras = frag
                hover_texts.append(palabras)

            df = len(z_values) - 1
            x_vals = z_values
            y_vals = t.pdf(x_vals, df=df)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="markers",
                marker=dict(symbol="triangle-up", size=10, color="skyblue"),
                name="Fragmentos",
                hovertext=hover_texts,
                hoverinfo="text"
            ))

            tabla4_path = tabla_dir / f"tabla4_spi_dudoso_{modelo_tag}.csv"
            if tabla4_path.exists():
                df4 = pd.read_csv(tabla4_path)
                unknown_z = df4["SPI_normalizado_PT"].iloc[0]
                unknown_y = t.pdf(unknown_z, df=df)
                fig.add_trace(go.Scatter(
                    x=[unknown_z],
                    y=[unknown_y],
                    mode="markers",
                    marker=dict(symbol="circle", size=12, color="red"),
                    name="Unknown",
                    hovertext="Texto dudoso"
                ))

                st.plotly_chart(fig, use_container_width=True)

                # Mostrar resumen calculado
                st.subheader("Resumen del Análisis")
                mu = df_spi["SPI_normalizado"].mean()
                sigma = df_spi["SPI_normalizado"].std(ddof=1)
                juicio = "✅ Compatible con el estilo del autor." if abs(unknown_z) <= 2 else "❌ Alejado significativamente del estilo del autor."

                st.markdown(f"""
                **Modelo:** `{modelo_tag}`  
                **SPI_normalizado(Unknown):** {unknown_z:.2f}  
                **Media fragmentos:** {mu:.2f}  
                **Desviación estándar:** {sigma:.2f}  
                **Juicio:** {juicio}
                """)

        else:
            st.warning("No se encontró la tabla de SPI para fragmentos")

        # Descargar tablas
        st.subheader("Descargar resultados")
        for csv_file in sorted(tabla_dir.glob(f"*{modelo_tag}*.csv")):
            with open(csv_file, "rb") as f:
                st.download_button(
                    label=f"Descargar {csv_file.name}",
                    data=f,
                    file_name=csv_file.name,
                    mime="text/csv"
                )

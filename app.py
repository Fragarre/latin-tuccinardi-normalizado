import streamlit as st
from pathlib import Path
import subprocess
from PIL import Image
import sys

# === CONFIGURACION ===
base_dir = Path(__file__).resolve().parent  # ✅ Ruta relativa y portátil
data_dir = base_dir / "data"
tabla_dir = data_dir / "resultados" / "tablas"
figura_dir = data_dir / "resultados" / "figuras"
resumen_path = data_dir / "resultados" / "resumen_spi_zscore.md"
script_path = base_dir / "analisis_spi_completo.py"

st.set_page_config(page_title="Análisis de Autoría SPI", layout="centered")
st.subheader("Análisis de Autoría mediante SPI Normalizado V 1.01")

# === SIDEBAR ===
st.sidebar.header("Parámetros del Modelo")
st.sidebar.info("""
Recarga la aplicación para nuevos ficheros.
Pueden realizarse varias ejecuciones sobre los mismos textos, variando parámetros n y s y volviendo a 'Ejecutar Análisis'
""")
n = st.sidebar.selectbox("Selecciona longitud del n-grama (n)", [3, 4, 5, 6], index=1)
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
    fig_path = figura_dir / f"figura_t_{modelo_tag}.png"
    if fig_path.exists():
        fig_path.unlink()
    if resumen_path.exists():
        resumen_path.unlink()

    with st.spinner("Ejecutando análisis..."):
        result = subprocess.run([
            sys.executable, str(script_path), str(n), s_arg
        ], capture_output=True, text=True)
    

    if result.returncode != 0:
        st.error("Error en la ejecución del script:")
        st.code(result.stderr)
    else:
        st.success("Análisis completado correctamente")

        # Mostrar figura
        if fig_path.exists():
            st.image(Image.open(fig_path), caption=f"Distribución t – Modelo {modelo_tag}")
        else:
            st.warning("Figura no encontrada")

        # Mostrar resumen
        if resumen_path.exists():
            with open(resumen_path, encoding="utf-8") as f:
                resumen = f.read()
            st.subheader("Resumen del Análisis")
            st.markdown(resumen)
        else:
            st.warning("Resumen no disponible")

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

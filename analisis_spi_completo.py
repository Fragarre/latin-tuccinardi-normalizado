from pathlib import Path
import zipfile
import shutil
import pandas as pd
from collections import Counter
from scipy.stats import t, norm
import matplotlib.pyplot as plt
import numpy as np
import sys

# === PARÁMETROS DE ENTRADA ===
if len(sys.argv) < 3:
    print("Uso: python analisis_spi_completo.py <n> <s>")
    sys.exit(1)

n = int(sys.argv[1])
s_arg = sys.argv[2]
s = None if s_arg.lower() == "none" else int(s_arg)
modelo = f"n{n}_L{s if s is not None else 'ALL'}"

# === RUTAS ===
base_dir = Path(__file__).resolve().parent
data_dir = base_dir / "data"
zip_path = list((data_dir / "textos_ciertos").glob("*.zip"))[0]
dudoso_path = list((data_dir / "texto_dudoso").glob("*.txt"))[0]
fragmentos_dir = data_dir / "fragmentos"
resultados_dir = data_dir / "resultados"
tabla_dir = resultados_dir / "tablas"
figura_dir = resultados_dir / "figuras"
resumen_path = resultados_dir / "resumen_spi_zscore.md"

for folder in [fragmentos_dir, tabla_dir, figura_dir]:
    if folder.exists():
        for f in folder.glob("*"):
            f.unlink()
    folder.mkdir(parents=True, exist_ok=True)

# === FUNCIONES ===
def extract_ngrams(text: str, n: int) -> list:
    return [text[i:i+n] for i in range(len(text) - n + 1)]

def top_ngrams(text: str, n: int, s: int | None) -> set:
    ngrams = extract_ngrams(text, n)
    counter = Counter(ngrams)
    if s is None:
        return set(counter.keys())
    return set([ng for ng, _ in counter.most_common(s)])

def fragment_text_preserving_words(text: str, n_fragments: int) -> list:
    words = text.split()
    total_words = len(words)
    step = total_words // n_fragments
    return [" ".join(words[i:i+step]) for i in range(0, total_words, step)][:n_fragments]

def calcular_spi(set1: set, set2: set) -> int:
    return len(set1 & set2)

# === 1. Renombrar archivos de entrada ===
known_zip = data_dir / "Known.zip"
shutil.copy(zip_path, known_zip)

unknown_txt = data_dir / "Unknown.txt"
shutil.copy(dudoso_path, unknown_txt)

# === 2. Extraer y concatenar textos ciertos ===
temp_dir = data_dir / "textos_ciertos" / "tmp"
if temp_dir.exists():
    shutil.rmtree(temp_dir)
temp_dir.mkdir(parents=True)

with zipfile.ZipFile(known_zip, "r") as zip_ref:
    zip_ref.extractall(temp_dir)

known_text = " ".join([f.read_text(encoding="utf-8") for f in sorted(temp_dir.glob("*.txt"))])
(data_dir / "Known.txt").write_text(known_text, encoding="utf-8")

# === 3. Fragmentar texto Known adaptativamente ===
unknown_text = unknown_txt.read_text(encoding="utf-8")
fragment_size = len(unknown_text)  # tamaño en caracteres del texto dudoso
known_length = len(known_text)
# # PARA PRUEBAS 
# fragment_size = 3500



estimated_n = known_length // fragment_size

print(f"Fragment size {fragment_size}  Number of estimated fragments {estimated_n}")

# if estimated_n < 12 or estimated_n > 30:
#     n_fragments = 15
# else:
#     n_fragments = estimated_n

n_fragments = estimated_n

print(f"Number of actual fragments {n_fragments}")

fragmentos = fragment_text_preserving_words(known_text, n_fragments)
fragment_paths = []
for i, frag in enumerate(fragmentos, 1):
    path = fragmentos_dir / f"Known{i}.txt"
    path.write_text(frag.strip(), encoding="utf-8")
    fragment_paths.append(path)

# === 4. Crear perfiles de n-gramas ===
perfil_known = top_ngrams(known_text, n, s)
perfil_unknown = top_ngrams(unknown_text, n, s)
fragmentos_perfiles = {
    path.stem: top_ngrams(path.read_text(encoding="utf-8"), n, s)
    for path in fragment_paths
}

# === 5. Calcular SPI y normalizar ===
tabla3, tabla4 = [], []
spi_vals = [(nombre, calcular_spi(perfil, perfil_known)) for nombre, perfil in fragmentos_perfiles.items()]
df_spi = pd.DataFrame(spi_vals, columns=["Fragmento", "SPI"])
mu, sigma = df_spi["SPI"].mean(), df_spi["SPI"].std(ddof=1)

for _, row in df_spi.iterrows():
    z = (row["SPI"] - mu) / sigma
    tabla3.append({"Modelo": modelo, "Fragmento": row["Fragmento"], "SPI_normalizado": z})

spi_unknown = calcular_spi(perfil_unknown, perfil_known)
norm_unknown = (spi_unknown - mu) / sigma
tabla4.append({"Modelo": modelo, "SPI_normalizado_PT": norm_unknown})

# === 6. Gráfico t-Student o normal según número de fragmentos ===
x_frag = df_spi["SPI"].apply(lambda x: (x - mu) / sigma).values
n_frag = len(x_frag)
df_t = n_frag - 1
x_vals = np.linspace(min(x_frag)-2, max(x_frag)+2, 500)

if n_frag > 50:
    dist_label = "Distribución normal"
    y_vals = norm.pdf(x_vals, loc=0, scale=1)
    y_frag = norm.pdf(x_frag, loc=0, scale=1)
    y_unknown = norm.pdf(norm_unknown, loc=0, scale=1)
else:
    dist_label = "Distribución t"
    y_vals = t.pdf(x_vals, df_t, loc=0, scale=1)
    y_frag = t.pdf(x_frag, df_t)
    y_unknown = t.pdf(norm_unknown, df_t)

plt.figure(figsize=(10, 6))
plt.plot(x_vals, y_vals, label=dist_label)
plt.scatter(x_frag, y_frag, marker="^", label="Fragmentos")
plt.scatter(norm_unknown, y_unknown, marker="o", color="red", label="Unknown")
plt.axvline(0, color="gray", linestyle="--")
plt.title(f"{dist_label} – Modelo {modelo}")
plt.xlabel("SPI normalizado")
plt.ylabel("Densidad")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(figura_dir / f"figura_t_{modelo}.png")
plt.close()


# === 7. Guardar salidas ===
pd.DataFrame(tabla3).to_csv(tabla_dir / f"tabla3_spi_normalizados_{modelo}.csv", index=False)
pd.DataFrame(tabla4).to_csv(tabla_dir / f"tabla4_spi_dudoso_{modelo}.csv", index=False)

# juicio = "✅ Compatible con el estilo del autor." if abs(norm_unknown) <= 2 else "❌ Alejado significativamente del estilo del autor."

# Nuevo juicio detallado
abs_z = abs(norm_unknown)
if abs_z <= 2:
    juicio = "✅ Compatible con el estilo del autor."
elif abs_z <= 3:
    juicio = "⚠️ Alejado del estilo del autor."
elif abs_z <= 4:
    juicio = "❌ Significativamente alejado del estilo del autor."
else:
    juicio = "⛔ Muy alejado del estilo del autor."

resumen = [
    f"## Resumen SPI normalizado – Modelo {modelo}",
    f"- SPI_normalizado(Unknown): {norm_unknown:.2f}",
    f"- Media fragmentos: {mu:.2f}",
    f"- Desviación estándar: {sigma:.2f}",
    f"- Juicio: {juicio}"
]
with open(resumen_path, "w", encoding="utf-8") as f:
    f.write("\n".join(resumen))

print(f"✅ Análisis SPI completado para modelo {modelo}")

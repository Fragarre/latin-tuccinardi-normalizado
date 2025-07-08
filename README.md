
# Análisis de Autoría mediante SPI Normalizado

Este proyecto implementa un sistema completo de verificación de autoría basado en el método **Simplified Profile Intersection (SPI)**, con normalización estadística por **z-score**. El enfoque sigue fielmente la metodología descrita en el artículo de **Enrico Tuccinardi (2017)**, que a su vez se basa en el modelo estilométrico propuesto por **Potha & Stamatatos (2014)**.

## Fundamento teórico

El método SPI compara el estilo del texto dudoso (Unknown) con el de un conjunto de textos conocidos (Known) mediante el uso de **n-gramas de caracteres** (secuencias de n caracteres consecutivos). Cuanto más n-gramas comparte el texto dudoso con los textos del autor conocido, más probable es que comparta su estilo.

Para estimar si un texto dudoso es compatible con el estilo del autor conocido:
1. Se fragmenta el texto conocido en partes de tamaño similar al texto dudoso.
2. Se extraen los **n-gramas más frecuentes** del texto conocido (parámetro `s`) con longitud `n`.
3. Se calcula el **SPI** entre cada fragmento y el perfil del autor, así como entre el texto dudoso y el mismo perfil.
4. Se normalizan los valores mediante la fórmula del **z-score**.
5. Se ajustan los resultados a una **distribución t de Student** para valorar si el texto dudoso cae dentro del estilo del autor o está significativamente alejado.

## Estructura funcional del script

El sistema está implementado como un único script Python (`analisis_spi_completo.py`) que ejecuta todo el proceso de forma automática:

### 1. Entrada de datos
- Un archivo `.zip` con los textos del autor conocido (`Known.zip`)
- Un archivo `.txt` con el texto de autoría dudosa (`Unknown.txt`)

Ambos ficheros pueden tener cualquier nombre: el script los renombra internamente como `Known` y `Unknown`.

### 2. Fragmentación
- Se calcula la longitud en caracteres del texto `Unknown`.
- Se divide el texto `Known` en fragmentos del mismo tamaño.
- Si el número de fragmentos resultantes es **menor de 15 o mayor de 30**, el script ajusta y genera exactamente 15 fragmentos de longitud similar.

### 3. Cálculo de perfiles de n-gramas
- Para cada fragmento y para los textos completos, se extraen los n-gramas de longitud `n`.
- Se seleccionan los `s` n-gramas más frecuentes para cada texto (o todos si `s=None`).

### 4. Cálculo del SPI
- Se calcula el **número de n-gramas comunes** entre cada fragmento y el perfil `Known`.
- Se hace lo mismo entre `Unknown` y `Known`.

### 5. Normalización y distribución t
- Los valores SPI de los fragmentos se normalizan mediante z-score:
  ```
  z = (SPI - media) / desviación_estándar
  ```
- Se ajusta la distribución de z-scores a una t de Student.

#### 🔢 ¿Por qué usar la distribución t de Student?
- La distribución t permite comparar el SPI del texto dudoso con los de los fragmentos, incluso cuando el número de fragmentos es pequeño.
- Es especialmente adecuada para muestras menores de 30 fragmentos.

## Resultados y visualización

El script genera:
- Tablas `.csv` con los SPI normalizados por fragmento y el valor de `Unknown`
- Un resumen `.md`
- Una figura `.png` que representa:
  - La curva t de Student
  - Los SPI normalizados de los fragmentos (flechas azules)
  - El SPI normalizado de `Unknown` (punto rojo)

### 🌐 Interpretación de la figura

En el eje X se representan los valores SPI normalizados (z-score). En el eje Y, su densidad según la distribución t. 

- Si el punto rojo (`Unknown`) cae **cerca del centro (entre -2 y +2)**, indica que su estilo es compatible con el del autor conocido.
- Si está **muy alejado** (por ejemplo, < -3 o > +3), se considera **muy poco probable que comparta el mismo estilo**.

### Ejemplos de salida gráfica

#### 1. Caso confiable
```
- SPI_normalizado(Unknown): -0.91
- Juicio: ✅ Compatible con el estilo del autor.
```
![Figura confiable](figura_ejemplo_confiable.png)

#### 2. Caso poco confiable
```
- SPI_normalizado(Unknown): -4.50
- Juicio: ❌ Alejado significativamente del estilo del autor.
```
![Figura no confiable](figura_ejemplo_no_confiable.png)

## Requisitos
- Python 3.10 o superior
- Paquetes: `pandas`, `numpy`, `matplotlib`, `scipy`

## Ejecución
```bash
python analisis_spi_completo.py 5 2000
```
- `5`: longitud del n-grama
- `2000`: número de n-gramas más frecuentes (usar `none` para no limitar)

## Licencia
Este proyecto se proporciona con fines académicos y de investigación. Inspirado en el trabajo de Enrico Tuccinardi y el método SPI de Potha & Stamatatos (2014).

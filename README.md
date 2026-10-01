# Finanzas

Programa de escritorio para llevar las finanzas personales: registra ingresos, gastos y ahorro, y muestra resúmenes por **semana, mes y año**, además de comparar lo **planeado contra lo real**.

Está hecho en **Python** con una interfaz de ventanas (**PySide6**) y guarda todo en una base de datos **SQLite** local. Es de uso personal: no necesita internet ni cuentas, y los datos se quedan en tu computadora.

---

## Contenido

1. [Qué hace](#qué-hace)
2. [Reglas del programa](#reglas-del-programa)
3. [Requisitos y librerías](#requisitos-y-librerías)
4. [Instalación y ejecución](#instalación-y-ejecución)
5. [Estructura de carpetas](#estructura-de-carpetas)
6. [Arquitectura](#arquitectura)
7. [Esquema de la base de datos](#esquema-de-la-base-de-datos)
8. [Dónde se guardan los datos](#dónde-se-guardan-los-datos)
9. [Respaldos y exportación](#respaldos-y-exportación)
10. [Crear el ejecutable en Fedora 44](#crear-el-ejecutable-en-fedora-44)
11. [Crear el ejecutable en Windows](#crear-el-ejecutable-en-windows)
12. [Pruebas](#pruebas)
13. [Cómo extender el proyecto](#cómo-extender-el-proyecto)
14. [Solución de problemas](#solución-de-problemas)

---

## Qué hace

| Pestaña | Función |
|---|---|
| **Movimientos** | Tabla de ingresos, gastos y ahorro con filtros (fechas, tipo, texto), saldo corrido y captura/edición/borrado. Sin límite de líneas: carga por páginas al desplazarte |
| **Resumen** | Totales por **semana, mes o año**, con navegación anterior/siguiente, desglose por categoría y gráfica de gastos |
| **Planeado vs real** | Comparación de un mes (ingresos, gastos, ahorro, disponible) y tabla del año completo |
| **Presupuesto** | Captura de lo planeado para cada mes del año |
| **Categorías** | Categorías **por año**; permite copiarlas del año anterior, renombrarlas y desactivarlas |
| **Pendientes** | Cosas todavía sin fecha (por ejemplo una compra futura); se convierten en reales cuando ocurren |

Menús: exportar a CSV/Excel, crear y restaurar respaldos, y elegir si la semana empieza en lunes o domingo.

Colores en la tabla de movimientos: **rojo** = movimiento de un periodo anterior, **azul** = pendiente, **verde** = ingreso.

---

## Reglas del programa

- **Disponible = ingresos − gastos − ahorro.** Es la única fórmula, tanto para lo planeado como para lo real. El ahorro **no** cuenta como ingreso.
- **Diferencia = real − planeado.**
- Los **pendientes** no afectan ningún total ni el saldo hasta que se marcan como reales.
- Las **categorías son por año**: una categoría de 2026 no se puede usar en un movimiento fechado en 2027.
- Cada movimiento guarda **dos fechas**: la del movimiento (editable, por defecto hoy) y la de **captura** (automática, no editable).
- **El dinero se guarda en centavos** (enteros) para evitar errores de redondeo. 150.50 se guarda como `15050`.
- Los movimientos **no se borran en cascada**: una categoría que ya se usó no se elimina, solo se **desactiva**.
- Un movimiento **real** siempre tiene fecha; uno **pendiente** puede no tenerla.
- La **semana** empieza en lunes por defecto (configurable a domingo). Una semana puede incluir días de dos meses.

---

## Requisitos y librerías

### Del sistema

- **Python 3.10 o superior** (recomendado **3.13**; las versiones más recientes a veces tardan en tener paquetes compatibles).
- **SQLite**: viene incluido con Python (módulo `sqlite3`).

### Librerías de Python

Archivo `requirements.txt` (necesarias para ejecutar):

| Librería | Para qué se usa |
|---|---|
| `PySide6` | Interfaz gráfica (ventanas, tablas y gráficas con QtCharts) |
| `platformdirs` | Encuentra la carpeta de datos correcta en cada sistema operativo |
| `openpyxl` | Exportar a Excel (`.xlsx`) |

Archivo `requirements-dev.txt` (solo para desarrollar):

| Librería | Para qué se usa |
|---|---|
| `pytest` | Pruebas automáticas |
| `ruff` | Revisión y formato del código |
| `pyinstaller` | Crear el ejecutable |

Módulos de la biblioteca estándar usados (no se instalan): `sqlite3`, `datetime`, `decimal`, `csv`, `dataclasses`, `enum`, `pathlib`.

### Paquetes del sistema en Fedora 44

Qt necesita algunas librerías para abrir ventanas:

```bash
sudo dnf upgrade --refresh -y
sudo dnf install -y python3 python3-pip python3-devel git sqlite binutils
sudo dnf install -y xcb-util-cursor xcb-util-image xcb-util-keysyms xcb-util-renderutil xcb-util-wm libxkbcommon-x11 mesa-libGL mesa-libEGL fontconfig
```

`binutils` lo necesita PyInstaller; el paquete `sqlite` da el comando `sqlite3` para inspeccionar la base.

### Editor recomendado: VS Code

```bash
sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
printf "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\nautorefresh=1\ntype=rpm-md\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc\n" | sudo tee /etc/yum.repos.d/vscode.repo > /dev/null
sudo dnf install -y code

code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension charliermarsh.ruff
code --install-extension qwtel.sqlite-viewer
```

La extensión *SQLite Viewer* permite abrir el archivo `.db` dentro de VS Code.

---

## Instalación y ejecución

```bash
cd ~/proyectos/finanzas

# 1. Entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Dependencias
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt -r requirements-dev.txt

# 3. Instalar el proyecto en modo editable (necesario por la carpeta src/)
pip install -e .

# 4. Ejecutar
python main.py
```

Cada vez que abras una terminal nueva, activa el entorno con `source .venv/bin/activate` (VS Code lo hace solo al elegir el intérprete `.venv`).

`requirements.lock.txt` guarda las versiones exactas con las que se probó en Linux (`pip freeze`). Úsalo solo en Linux; en Windows instala desde `requirements.txt`.

**Primera ejecución:** el programa crea la carpeta de datos y la base, y si el año actual no tiene categorías, copia las del año anterior o crea unas básicas (Sueldo, Extras, Transporte, Entretenimiento, Pagos, Gastos generales, Gasto hormiga, Ahorro), todas editables.

---

## Estructura de carpetas

```
finanzas/
├── main.py                      Punto de entrada (casi vacío)
├── pyproject.toml               Configuración del paquete y de pytest
├── requirements.txt             Dependencias para ejecutar
├── requirements-dev.txt         Dependencias de desarrollo
├── requirements.lock.txt        Versiones exactas (Linux)
├── construir.sh                 Script para reconstruir el ejecutable en Linux
├── README.md
├── .gitignore
├── .vscode/settings.json        Intérprete de Python para VS Code
├── src/finanzas/
│   ├── app.py                   Aplicacion: arma todas las piezas y abre la ventana
│   ├── contenedor.py            Servicios: agrupa los servicios para la interfaz
│   ├── rutas.py                 Rutas: dónde se guardan datos, respaldos y exportaciones
│   ├── excepciones.py           Errores propios (ErrorValidacion, ErrorNoEncontrado)
│   │
│   ├── datos/                   CAPA DE DATOS (único lugar con SQL)
│   │   ├── base_datos.py        BaseDatos: conexión SQLite y transacciones
│   │   ├── esquema.py           Esquema: tablas, vistas y migraciones
│   │   ├── repo_categorias.py   RepositorioCategorias
│   │   ├── repo_movimientos.py  RepositorioMovimientos
│   │   ├── repo_presupuesto.py  RepositorioPresupuesto
│   │   ├── repo_configuracion.py RepositorioConfiguracion
│   │   └── respaldos.py         GestorRespaldos
│   │
│   ├── logica/                  CAPA DE LÓGICA (reglas y cálculos, sin ventanas)
│   │   ├── modelos.py           Clases de datos y enumeraciones
│   │   ├── dinero.py            Dinero: pesos ↔ centavos y formato
│   │   ├── periodos.py          CalculadoraPeriodos: semana, mes y año
│   │   ├── servicio_categorias.py
│   │   ├── servicio_movimientos.py
│   │   ├── servicio_presupuesto.py
│   │   ├── servicio_resumen.py  Resúmenes, planeado vs real, saldo corrido
│   │   └── servicio_exportacion.py
│   │
│   └── interfaz/                CAPA DE INTERFAZ (PySide6)
│       ├── ventana_principal.py VentanaPrincipal: pestañas y menús
│       ├── vista_movimientos.py
│       ├── vista_resumen.py
│       ├── vista_comparativo.py
│       ├── vista_presupuesto.py
│       ├── vista_categorias.py
│       ├── vista_pendientes.py
│       ├── dialogo_movimiento.py Formulario de captura y edición
│       ├── modelo_tabla_movimientos.py Tabla con carga por páginas
│       ├── grafica_resumen.py   Gráfica de pastel
│       └── estilos.py           Colores y ayudas para tablas
└── tests/                       Pruebas automáticas (pytest)
    ├── conftest.py
    ├── test_dinero.py
    ├── test_periodos.py
    ├── test_repo_movimientos.py
    ├── test_servicio_movimientos.py
    └── test_servicio_resumen.py
```

---

## Arquitectura

El flujo va en una sola dirección y cada capa solo conoce a la de abajo:

```
Interfaz  →  Servicios (lógica)  →  Repositorios (datos)  →  SQLite
```

- La **interfaz** nunca escribe SQL ni hace cuentas: pide cosas a los servicios.
- Los **servicios** contienen las reglas y los cálculos, y no saben que existe una ventana.
- Los **repositorios** son los únicos que hablan SQL.
- `Aplicacion` (en `app.py`) crea todo y pasa cada pieza a quien la necesita. Por eso `main.py` solo tiene dos líneas útiles.

Esta separación permite probar la lógica con pytest sin abrir ninguna ventana, y cambiar la interfaz sin tocar los cálculos.

**Principio clave:** solo se guardan **movimientos**. Los subtotales, cortes, resúmenes y saldos se **calculan** al momento, por lo que nunca se desajustan.

---

## Esquema de la base de datos

Archivo: `finanzas.db` (SQLite). Se crea y actualiza solo.

```
categorias 1 ──────< N movimientos

presupuesto_mensual      (independiente, una fila por año y mes)
configuracion            (clave/valor)
```

### Tabla `categorias`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | INTEGER PK | Autoincremental |
| `anio` | INTEGER | Año al que pertenece la categoría |
| `nombre` | TEXT | Sin distinguir mayúsculas (`COLLATE NOCASE`) |
| `tipo` | TEXT | `ingreso`, `gasto` o `ahorro` |
| `es_hormiga` | INTEGER | 0 o 1 (solo tiene sentido en gastos) |
| `activa` | INTEGER | 0 o 1; se desactiva en lugar de borrar |

Restricción: `UNIQUE (anio, nombre, tipo)`.

### Tabla `movimientos`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | INTEGER PK | Autoincremental |
| `descripcion` | TEXT | Obligatoria |
| `monto` | INTEGER | **Centavos**, siempre positivo (`CHECK monto > 0`) |
| `categoria_id` | INTEGER | FK → `categorias(id)`. El tipo se obtiene de la categoría |
| `fecha_movimiento` | TEXT | `AAAA-MM-DD`, editable. Puede ser NULL solo si es pendiente |
| `fecha_captura` | TEXT | `AAAA-MM-DD HH:MM:SS`, automática |
| `estado` | TEXT | `real` o `pendiente` |
| `es_anterior` | INTEGER | 0 o 1 (movimiento de un periodo anterior) |
| `notas` | TEXT | Opcional |

Restricción: un movimiento es `pendiente` **o** tiene `fecha_movimiento`.
Índices: `fecha_movimiento`, `categoria_id`, `estado`.

### Tabla `presupuesto_mensual`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | INTEGER PK | |
| `anio` | INTEGER | |
| `mes` | INTEGER | 1 a 12 |
| `ingresos_planeados` | INTEGER | Centavos |
| `gastos_planeados` | INTEGER | Centavos |
| `ahorro_planeado` | INTEGER | Centavos |

Restricción: `UNIQUE (anio, mes)`. El disponible planeado se calcula, no se guarda.

### Tabla `configuracion`

| Columna | Tipo | Notas |
|---|---|---|
| `clave` | TEXT PK | |
| `valor` | TEXT | |

Claves actuales: `inicio_semana` (`lunes` o `domingo`) y `moneda`.

### Vistas

- `v_movimientos_detalle`: movimientos unidos con su categoría (nombre, tipo, hormiga). Es la base de todas las consultas de lectura.
- `v_resumen_mensual`: ingresos, gastos y ahorro reales por año y mes. Útil para consultar a mano desde VS Code.

### Reglas de la conexión

- `PRAGMA foreign_keys = ON` en cada conexión.
- `PRAGMA journal_mode = WAL` (por eso puedes ver archivos `finanzas.db-wal` y `finanzas.db-shm` junto a la base; es normal).
- La versión del esquema se guarda en `PRAGMA user_version` (actualmente **1**).

---

## Dónde se guardan los datos

Los datos **nunca** viven dentro del ejecutable, así que puedes actualizar o reinstalar el programa sin perder nada.

| Sistema | Carpeta |
|---|---|
| Linux (Fedora) | `~/.local/share/finanzas/` |
| Windows | `C:\Users\<usuario>\AppData\Local\finanzas\finanzas\` |

Contenido de la carpeta:

```
finanzas.db        Base de datos
respaldos/         Copias de seguridad (finanzas_AAAAMMDD_HHMMSS.db)
exportaciones/     Carpeta sugerida para CSV y Excel exportados
```

Para pasar tus datos de un sistema a otro, usa un respaldo (menú **Archivo → Crear respaldo ahora**) y restáuralo en el otro sistema (**Archivo → Restaurar respaldo…**).

---

## Respaldos y exportación

- **Respaldo automático:** al abrir el programa, si el último respaldo tiene más de 24 horas, se crea uno nuevo. Se conservan los 15 más recientes.
- **Respaldo manual:** menú Archivo → Crear respaldo ahora.
- **Restaurar:** menú Archivo → Restaurar respaldo…. Antes de reemplazar los datos, el programa guarda una copia de lo actual.
- **Exportar:** menú Archivo → Exportar movimientos… o Exportar resumen del año…, en `.xlsx` o `.csv`. Los CSV usan UTF-8 con BOM para que Excel y LibreOffice lean bien los acentos.

---

## Crear el ejecutable en Fedora 44

Con el entorno virtual activo y la carpeta del proyecto como directorio actual.

### 1. Comprobar que el programa abre

```bash
python main.py
```

### 2. Empaquetar con PyInstaller

```bash
pyinstaller --noconfirm --clean --name finanzas --paths src --collect-submodules finanzas main.py
```

- No se usa `--onefile` a propósito: con Qt arranca más lento porque se descomprime en cada apertura.
- El resultado queda en `dist/finanzas/` y el ejecutable es `dist/finanzas/finanzas`.

```bash
./dist/finanzas/finanzas
```

### 3. Instalar en tu carpeta de usuario (sin sudo)

```bash
mkdir -p ~/.local/opt
rm -rf ~/.local/opt/finanzas
cp -r dist/finanzas ~/.local/opt/finanzas
```

### 4. Crear el ícono

```bash
mkdir -p ~/.local/share/icons/hicolor/scalable/apps
cat > ~/.local/share/icons/hicolor/scalable/apps/finanzas.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="26" fill="#2e7d32"/>
  <text x="64" y="90" font-size="80" font-family="sans-serif" font-weight="bold" text-anchor="middle" fill="#ffffff">$</text>
</svg>
EOF
```

### 5. Crear el lanzador del menú de aplicaciones

El `EOF` va **sin comillas** a propósito para que `$HOME` se reemplace por tu ruta real.

```bash
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/finanzas.desktop << EOF
[Desktop Entry]
Type=Application
Name=Finanzas
Comment=Control de ingresos, gastos y ahorro
Exec=$HOME/.local/opt/finanzas/finanzas
Icon=finanzas
Terminal=false
Categories=Office;Finance;
StartupWMClass=finanzas
EOF
chmod +x ~/.local/share/applications/finanzas.desktop
update-desktop-database ~/.local/share/applications 2>/dev/null || true
```

Busca "Finanzas" en el menú de aplicaciones (si no aparece, cierra sesión y vuelve a entrar).

### 6. Opcional: comando `finanzas` en la terminal

```bash
mkdir -p ~/.local/bin
ln -sf ~/.local/opt/finanzas/finanzas ~/.local/bin/finanzas
```

### 7. Actualizar después de cambiar el código

`construir.sh` (en la raíz del proyecto):

```bash
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
pyinstaller --noconfirm --clean --name finanzas --paths src --collect-submodules finanzas main.py
rm -rf ~/.local/opt/finanzas
cp -r dist/finanzas ~/.local/opt/finanzas
echo "Listo: finanzas actualizado."
```

```bash
chmod +x construir.sh
./construir.sh
```

---

## Crear el ejecutable en Windows

PyInstaller **no compila de Linux a Windows**: el `.exe` hay que generarlo *en* Windows. El código no necesita cambios.

### Opción A: en una PC o máquina virtual con Windows

1. Instala **Python 3.13** desde python.org y marca "Add python.exe to PATH".
2. Copia el proyecto a Windows (por Git o ZIP, **sin** la carpeta `.venv`).
3. En **PowerShell**, dentro de la carpeta del proyecto:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
pyinstaller --noconfirm --clean --windowed --name finanzas --paths src --collect-submodules finanzas main.py
```

- Usa `requirements.txt` y `requirements-dev.txt`, **no** `requirements.lock.txt` (se generó en Linux).
- `--windowed` evita que se abra una consola negra junto a la ventana.
- Si PowerShell bloquea la activación del entorno: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

El ejecutable queda en `dist\finanzas\finanzas.exe`. Para llevarlo a otra PC, comprime **toda la carpeta** `dist\finanzas` en un ZIP; el `.exe` solo no funciona.

### Opción B: sin Windows, con GitHub Actions

Crea `.github/workflows/windows.yml`:

```yaml
name: Ejecutable de Windows

on:
  workflow_dispatch:

jobs:
  construir:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Instalar dependencias
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt -r requirements-dev.txt
      - name: Empaquetar
        run: pyinstaller --noconfirm --clean --windowed --name finanzas --paths src --collect-submodules finanzas main.py
      - uses: actions/upload-artifact@v4
        with:
          name: finanzas-windows
          path: dist/finanzas
```

Sube los cambios a GitHub, entra a la pestaña **Actions**, elige "Ejecutable de Windows" y pulsa **Run workflow**. Al terminar, descarga `finanzas-windows` desde esa misma página.

### Notas para Windows

- **SmartScreen** mostrará un aviso de "editor desconocido" porque el programa no está firmado. Para uso personal: Más información → Ejecutar de todas formas.
- Los datos de Windows y de Linux son archivos distintos; para moverlos usa los respaldos.

---

## Pruebas

```bash
pytest
```

Cubren la lógica y la base de datos: dinero, periodos (semanas con inicio en lunes y domingo), repositorio de movimientos, reglas de validación, resúmenes, planeado vs real, saldo corrido y exportación. La interfaz no tiene pruebas automáticas; se revisa abriendo el programa.

Revisión y formato del código:

```bash
ruff check src tests
ruff format src tests
```

---

## Cómo extender el proyecto

**Agregar una columna o tabla a la base de datos**
1. En `datos/esquema.py`, sube `VERSION_ACTUAL` (de 1 a 2).
2. Agrega el script en `MIGRACIONES`, por ejemplo:
   `{2: "ALTER TABLE movimientos ADD COLUMN etiqueta TEXT;"}`.
3. Actualiza el modelo (`logica/modelos.py`) y el repositorio correspondiente.

Las bases existentes se actualizan solas al abrir el programa; no se pierden datos.

**Agregar una pestaña nueva**
1. Crea `interfaz/vista_nueva.py` con una clase que reciba `servicios` y tenga un método `refrescar()`.
2. Regístrala en la lista de pestañas de `ventana_principal.py`.

**Agregar un cálculo o reporte nuevo:** va en un servicio de `logica/` (normalmente `servicio_resumen.py`), con su consulta en el repositorio y una prueba en `tests/`. No pongas cuentas dentro de la interfaz.

**Convenciones**
- Nombres de archivos, clases y funciones en español, sin acentos ni ñ en los identificadores.
- Dinero siempre en centavos dentro del programa; la conversión a pesos solo ocurre al mostrar (`Dinero.formato`) o al capturar (`Dinero.a_centavos`).
- Las clases de `datos/` son las únicas que escriben SQL.
- Los errores que debe ver la persona usuaria se lanzan como `ErrorValidacion` con un mensaje claro.

**Ideas para después:** presupuesto por categoría, alertas al pasarse de lo planeado, gráficas de barras por mes, movimientos recurrentes (suscripciones) y un instalador de Windows con Inno Setup.

---

## Solución de problemas

| Síntoma | Qué hacer |
|---|---|
| `ModuleNotFoundError: finanzas` al correr `python main.py` | Falta `pip install -e .` con el entorno activo |
| `pip` no encuentra versión de PySide6 o PyInstaller | Tu Python es demasiado nuevo: instala `python3.13` (`sudo dnf install -y python3.13`) y crea el entorno con `python3.13 -m venv .venv` |
| La ventana no abre y no hay error (Linux) | Prueba con X11: `QT_QPA_PLATFORM=xcb python main.py` |
| `Could not load the Qt platform plugin "xcb"` | Falta alguna librería del sistema: repite la instalación de paquetes de Fedora |
| `ModuleNotFoundError` dentro del ejecutable | Agrega `--hidden-import nombre_del_modulo` al comando de PyInstaller |
| La gráfica del Resumen no aparece en el ejecutable | Agrega `--collect-all PySide6` al comando (el paquete crece, pero incluye todo Qt) |
| `pyinstaller: command not found` | Activa el entorno: `source .venv/bin/activate` |
| «La base de datos es de una versión más nueva» | Estás abriendo una base creada con una versión más reciente del programa: actualiza el programa |
| Aparecen `finanzas.db-wal` y `finanzas.db-shm` | Es normal (modo WAL de SQLite); no los borres con el programa abierto |
| Quiero empezar desde cero | Cierra el programa y borra `finanzas.db` (y los `-wal`/`-shm`) de la carpeta de datos |

---

## Notas

- Proyecto de uso personal; los datos viven solo en tu equipo.
- Las carpetas `build/`, `dist/` y `.venv/` y los archivos `*.db` están en `.gitignore`: no se suben a Git.

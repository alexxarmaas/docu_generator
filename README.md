# Docu Generator

Workspace local-first para crear, anotar, versionar y publicar documentación de producto.

Desde la versión 0.4 la interfaz principal es **Next.js + React** y el motor de publicación sigue en **Python**. Streamlit se mantiene como interfaz legacy mientras termina la transición.

## Arquitectura

```text
Next.js / React
├── editor de pasos y bloques
├── drag & drop
├── editor visual de capturas
├── autosave
├── biblioteca de proyectos
└── preview
        │
        ▼
FastAPI local :8787
├── proyectos / versiones
├── migración v1-v4
├── validación
├── render de anotaciones
└── exportación
        │
        ▼
PDF · DOCX · HTML · Markdown · ZIP
```

Los proyectos continúan siendo archivos portables `.docugen.json`.

## Arranque en Windows

Requiere:

- Python 3.11 o superior.
- Node.js 24 recomendado.

Desde la raíz del repositorio:

```bat
git pull
dev.bat
```

La primera ejecución:

1. crea `.venv` si no existe;
2. instala/actualiza el backend Python;
3. instala el frontend si falta `node_modules`;
4. arranca FastAPI en `http://127.0.0.1:8787`;
5. arranca Next.js en `http://localhost:3000`.

Abre:

```text
http://localhost:3000
```

## Arranque manual

Backend:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python -m uvicorn docu_generator.api:app --reload --host 127.0.0.1 --port 8787
```

Frontend, en otra terminal:

```bat
cd frontend
npm install
npm run dev
```

## Editor React

La interfaz principal permite:

- crear pasos;
- añadir bloques;
- reordenar bloques mediante drag & drop;
- mover bloques entre pasos arrastrándolos;
- duplicar y eliminar bloques;
- texto;
- imágenes;
- checklists;
- tablas;
- avisos;
- separadores;
- saltos de página;
- deshacer / rehacer;
- autosave;
- biblioteca local;
- publicar versiones;
- validación;
- exportación.

## Editor visual de capturas

Una imagen puede contener anotaciones no destructivas:

- rectángulos;
- flechas;
- números;
- blur;
- recorte.

Las posiciones se guardan normalizadas, por lo que no dependen del tamaño al que se muestra la captura.

Ejemplo conceptual:

```text
Captura original
      +
anotaciones vectoriales
      +
recorte
      │
      ▼
render Python al exportar
      │
      ▼
imagen final PDF / DOCX / HTML / ZIP
```

El proyecto conserva la imagen original y las instrucciones de anotación. Las modificaciones no se queman de forma irreversible en el archivo editable.

## Formato de proyecto v4

El formato actual es **v4**.

Además de los datos anteriores, cada bloque de imagen puede almacenar:

```json
{
  "annotations": [
    {
      "id": "a1",
      "type": "arrow",
      "x": 0.12,
      "y": 0.30,
      "x2": 0.72,
      "y2": 0.64,
      "color": "#00B8A9"
    }
  ],
  "crop": {
    "x": 0.05,
    "y": 0.05,
    "width": 0.9,
    "height": 0.8
  }
}
```

La API migra automáticamente:

```text
v1 ─┐
v2 ─┼─> v4
v3 ─┘
```

Esto también se aplica al importar un proyecto antiguo desde el frontend.

## Workspace local

Los proyectos continúan guardándose en:

```text
~/DocuGenerator/
├── autosave.docugen.json
├── projects/
└── versions/
```

El navegador no necesita una cuenta ni una base de datos externa. El backend local se encarga de la persistencia.

## Publicación

### PDF

Generado con ReportLab.

Incluye:

- portada;
- índice;
- metadatos;
- pasos;
- imágenes anotadas;
- tablas;
- checklists;
- callouts;
- saltos de página;
- footer;
- versión;
- paginación.

### DOCX

Generado con `python-docx`.

Las capturas se renderizan con sus anotaciones antes de insertarse, mientras que el resto del documento sigue siendo editable en Word.

### HTML

Documento autónomo con imágenes embebidas y CSS de impresión.

### Markdown

Salida ligera para repositorios, wikis o documentación técnica.

### ZIP

Incluye:

```text
guide.pdf
guide.docx
guide.html
guide.md
review.txt
images/
```

## Backend API

Endpoints principales:

```text
GET  /api/health
POST /api/normalize
GET  /api/autosave
POST /api/autosave
GET  /api/projects
GET  /api/projects/{name}
POST /api/projects
DELETE /api/projects/{name}
GET  /api/projects/{name}/versions
GET  /api/projects/{name}/versions/{version}
POST /api/validate
POST /api/export/pdf
POST /api/export/docx
POST /api/export/html
POST /api/export/md
POST /api/export/zip
```

La documentación OpenAPI puede verse con el backend activo en:

```text
http://127.0.0.1:8787/docs
```

## Streamlit legacy

La aplicación anterior sigue disponible temporalmente:

```bat
streamlit run app.py
```

No es ya la interfaz objetivo para nuevas funcionalidades visuales.

## Desarrollo y CI

La CI valida ambos stacks:

```text
Python
├── install
├── compileall
└── pytest

Node
├── npm install
├── tsc --noEmit
└── next build
```

El frontend usa React 19, Next.js 16, dnd-kit y React-Konva. El backend mantiene la lógica de documentos, render y exportación centralizada para evitar duplicarla entre interfaces.

# Docu Generator

Workspace local-first para crear, versionar y publicar documentación de producto mediante pasos y bloques reutilizables.

La aplicación funciona sin API. La IA queda como una capacidad opcional del proyecto, no como dependencia del editor.

## Estado actual

Docu Generator incluye:

- Editor por pasos.
- Bloques libres y colapsables.
- Texto, imágenes, checklists, tablas, avisos, separadores y saltos de página.
- Presets reutilizables:
  - Consejo.
  - Importante.
  - Resultado esperado.
  - Antes de continuar.
- Reordenar, duplicar, borrar, copiar y mover bloques entre pasos.
- Tamaño y alineación de imágenes.
- Deshacer / rehacer.
- Autosave local.
- Recuperación automática de la última sesión.
- Biblioteca local de proyectos.
- Historial de versiones al guardar.
- Plantillas completas:
  - En blanco.
  - Tutorial paso a paso.
  - Procedimiento operativo.
  - Resolución de problemas.
  - Primeros pasos.
- Metadatos:
  - Tipo.
  - Versión.
  - Estado.
  - Autor.
  - Portada.
  - Índice.
- Validación antes de exportar.
- Migración automática de proyectos v1 y v2 al formato v3.
- Exportación a:
  - PDF.
  - DOCX.
  - HTML autónomo.
  - Markdown.
  - ZIP completo.
  - Proyecto editable `.docugen.json`.

## Puesta en marcha

Requiere Python 3.11 o superior.

```bat
git clone https://github.com/alexxarmaas/docu_generator.git
cd docu_generator

python -m venv .venv
.venv\Scripts\activate

pip install -e .
streamlit run app.py
```

Normalmente se abrirá en:

```text
http://localhost:8501
```

## Workspace local

Docu Generator crea automáticamente:

```text
~/DocuGenerator/
├── autosave.docugen.json
├── projects/
└── versions/
```

El autosave permite recuperar la última sesión.

Cada guardado manual en la biblioteca crea además una copia histórica en `versions/`.

## Modelo de documento

```text
Documento
├── Metadatos
│   ├── Tipo
│   ├── Versión
│   ├── Estado
│   └── Autor
├── Portada opcional
├── Índice opcional
├── Introducción
├── Paso 1
│   ├── Texto
│   ├── Imagen
│   ├── Consejo
│   ├── Tabla
│   ├── Checklist
│   └── ...
├── Paso 2
│   └── ...
└── Cierre
```

## Bloques

### Texto

Admite Markdown básico.

### Imagen

Permite definir:

- Pie de foto.
- Tamaño pequeño, mediano, grande o ancho completo.
- Alineación izquierda, centro o derecha.

### Checklist

Un elemento por línea.

### Tabla

Una fila por línea y columnas separadas por `|`.

Ejemplo:

```text
Campo | Descripción | Ejemplo
Proveedor | Proveedor del documento | ACME S.L.
Fecha | Fecha del albarán | 23/09/2026
```

### Callouts

- Información.
- Consejo.
- Advertencia.
- Resultado esperado.

### Salto de página

Fuerza un salto en PDF, DOCX y modo impresión HTML.

## Exportación

### PDF

Generación local con ReportLab.

Incluye:

- Portada.
- Índice.
- Metadatos.
- Pasos.
- Imágenes.
- Tablas.
- Checklists.
- Callouts.
- Saltos de página.
- Footer con versión y paginación.

### DOCX

Generación local con `python-docx`.

Es editable posteriormente en Word o LibreOffice.

### HTML

Documento autónomo con imágenes embebidas.

Incluye CSS de impresión.

### ZIP

Contiene:

```text
guide.pdf
guide.docx
guide.html
guide.md
review.txt
images/
```

## Perfil Brisia

El primer perfil incluido es:

```text
profiles/
└── brisia/
    ├── profile.yaml
    └── style.css
```

Define identidad visual e instrucciones de producto.

La arquitectura permite añadir nuevos perfiles sin modificar el editor.

## Formato de proyecto

El formato actual es **v3**.

Los proyectos antiguos se migran automáticamente:

```text
v1 -> v3
v2 -> v3
```

Las imágenes se almacenan dentro del propio JSON para que el archivo sea portable.

## Desarrollo

CI:

```text
instalación
    ↓
compileall
    ↓
pytest
```

El editor local es el flujo principal. El pipeline experimental de IA permanece desacoplado y puede utilizarse más adelante como ayuda opcional.

# Docu Generator

Editor local-first para crear guías de usuario mediante pasos y bloques reutilizables.

El objetivo es poder construir documentación visual de producto sin depender de una API. La IA puede añadirse como ayuda opcional, pero el flujo principal funciona completamente en local.

## Funcionalidades

- Editor de guías por pasos.
- Bloques libres dentro de cada paso.
- Bloques colapsables.
- Reordenación, duplicado y eliminación.
- Inserción de contenido entre bloques.
- Imágenes con pie de foto.
- Checklists.
- Separadores.
- Biblioteca de callouts reutilizables:
  - Consejo.
  - Importante.
  - Resultado esperado.
  - Antes de continuar.
- Vista previa en tiempo real.
- Guardar y abrir proyectos `.docugen.json`.
- Compatibilidad automática con proyectos v1.
- Exportación local a:
  - PDF.
  - HTML autónomo.
  - Markdown.
  - ZIP completo con PDF, HTML, Markdown e imágenes.
- Perfil visual de Brisia.

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

La aplicación estará disponible normalmente en:

```text
http://localhost:8501
```

## Modelo de documento

```text
Guía
├── Título
├── Introducción
├── Paso 1
│   ├── Texto
│   ├── Imagen
│   ├── Consejo
│   ├── Checklist
│   └── ...
├── Paso 2
│   └── ...
└── Cierre
```

Los bloques pueden aparecer en cualquier orden y repetirse tantas veces como sea necesario.

## PDF

La exportación PDF se genera localmente con ReportLab. No necesita navegador, servidor externo ni API.

El PDF utiliza el mismo contenido de bloques que HTML y Markdown, incluyendo:

- Títulos de pasos.
- Texto.
- Imágenes.
- Checklists.
- Callouts.
- Separadores.
- Pies de imagen.
- Paginación.

## Proyectos

El formato `.docugen.json` contiene el documento completo, incluidas las imágenes codificadas dentro del propio archivo.

Esto permite guardar una guía, cerrar Docu Generator y continuar editándola posteriormente sin depender de archivos externos.

## Perfil Brisia

El diseño exportado utiliza actualmente el perfil:

```text
profiles/
└── brisia/
    ├── profile.yaml
    └── style.css
```

La arquitectura permite añadir otros perfiles sin cambiar el editor.

## Desarrollo

La CI ejecuta:

```text
instalación
    ↓
compileall
    ↓
pytest
```

El proyecto mantiene compatibilidad con el pipeline de generación experimental, pero el editor local por bloques es el flujo principal.

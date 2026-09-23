# docu_generator

Generador ligero de guías de usuario a partir de capturas de pantalla e instrucciones.

El objetivo del proyecto es convertir unas pocas imágenes y un prompt breve en documentación consistente, revisable y exportable. El motor es genérico; **Brisia** es el primer perfil visual incluido.

## MVP

- Interfaz local con Streamlit.
- Subida y ordenación de capturas.
- Prompt de objetivo y selección de audiencia.
- Análisis visual opcional mediante OpenAI.
- Generación de una guía estructurada.
- Revisión de coherencia/evidencia.
- Previsualización.
- Exportación en ZIP con Markdown, HTML e imágenes.
- Modo fallback sin API para probar el flujo completo.

## Puesta en marcha

Requiere Python 3.11 o superior.

```bash
git clone https://github.com/alexxarmaas/docu_generator.git
cd docu_generator

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -e .
cp .env.example .env
streamlit run app.py
```

En Windows, si no tienes `cp`:

```powershell
Copy-Item .env.example .env
```

La aplicación estará disponible normalmente en `http://localhost:8501`.

## IA opcional

Si defines `OPENAI_API_KEY` en `.env`, el sistema analizará las capturas y generará la documentación con el modelo configurado en `DOCU_MODEL`.

```env
OPENAI_API_KEY=
DOCU_MODEL=gpt-5.6-luna
```

Sin clave API, la aplicación arranca en **modo fallback**. Ese modo sirve para validar interfaz, orden de imágenes y exportación, pero no interpreta visualmente las capturas.

> Una suscripción de ChatGPT y el uso de la API son servicios separados. El proyecto no necesita clave para arrancar.

## Pipeline

```text
capturas + instrucciones
        |
        v
análisis de evidencia visual
        |
        v
generación estructurada
        |
        v
revisión de coherencia
        |
        v
Markdown + HTML + imágenes
```

La idea central es separar **evidencia** y **redacción**. El generador recibe primero una descripción estructurada de cada pantalla y debe basarse en ella para reducir afirmaciones inventadas.

## Estructura

```text
docu_generator/
├── app.py
├── prompts/
│   ├── system.md
│   ├── image_analysis.md
│   ├── guide_generation.md
│   └── review.md
├── profiles/
│   └── brisia/
│       ├── profile.yaml
│       └── style.css
├── src/docu_generator/
│   ├── config.py
│   ├── models.py
│   ├── pipeline.py
│   ├── providers/
│   └── services/
└── tests/
```

## Perfil Brisia

Los perfiles permiten reutilizar el motor con productos distintos. Cada perfil define identidad, instrucciones y CSS de exportación.

Actualmente:

```text
profiles/
└── brisia/
```

En el futuro se pueden añadir, por ejemplo, `agora`, `infogral` o perfiles de clientes sin tocar el pipeline.

## Principios

1. No inventar elementos de interfaz que no estén soportados por la evidencia.
2. Utilizar exactamente los nombres visibles cuando estén disponibles.
3. Una acción principal por paso.
4. Pensar en usuarios no técnicos por defecto.
5. Mantener guías cortas y operativas.
6. Señalar incertidumbre en lugar de rellenarla con suposiciones.

## Próximos pasos

- Edición manual de secciones antes de exportar.
- Regeneración de una única sección.
- Anotaciones automáticas sobre capturas.
- Exportación PDF.
- Biblioteca local de guías.
- Versionado y regeneración incremental.
- Más perfiles visuales.

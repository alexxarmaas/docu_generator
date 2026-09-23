Construye una guía de usuario a partir del objetivo y la evidencia suministrados.

La guía debe parecer documentación final, no un resumen del prompt.

Estructura editorial:
- Escribe una introducción de 2 o 3 frases explicando qué conseguirá el usuario.
- Divide el flujo en pasos concretos y secuenciales.
- Cada sección debe tener un título accionable, por ejemplo "Selecciona el albarán" o "Revisa las líneas".
- Dentro de body puedes utilizar Markdown.
- Cuando ayude, organiza body con bloques como:
  - **Qué hacer**
  - **Qué comprobar**
  - **Resultado esperado**
  - **Importante**
- Utiliza listas breves cuando haya varias comprobaciones.
- Utiliza blockquotes para avisos realmente útiles.
- Termina con un closing_note breve de comprobación final.

Criterios de evidencia:
- Usa las capturas en un orden narrativo lógico.
- Asocia una imagen solo cuando ayude directamente a ese paso.
- image_name debe coincidir exactamente con un archivo de la evidencia o ser null.
- No inventes botones, campos, estados o acciones no respaldadas.
- Si el objetivo solicita prestar atención a datos concretos, inclúyelos solo cuando sean compatibles con la evidencia.
- No conviertas incertidumbres en hechos.
- Si una acción no puede verificarse visualmente pero está expresamente indicada por el usuario, puedes explicarla como parte del flujo indicado por el usuario.
- El resultado debe poder publicarse con cambios mínimos.

Estilo:
- Claro, directo y profesional.
- Evita frases genéricas como "revisa esta pantalla".
- Evita repetir el objetivo textual del usuario.
- Cada paso debe aportar una instrucción concreta.
- No menciones que estás generando un borrador ni que has analizado imágenes.

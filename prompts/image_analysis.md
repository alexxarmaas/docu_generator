Analiza la captura como evidencia para una futura guía de usuario.

Identifica únicamente aquello que puedas observar con suficiente confianza.

Necesito:
- screen_name: nombre breve y descriptivo de la pantalla.
- visible_elements: textos, botones, campos, tablas, estados o controles claramente visibles.
- supported_actions: acciones que la interfaz visible permite inferir de forma razonable.
- uncertainties: elementos relevantes que no puedas confirmar o cuyo significado sea ambiguo.

No redactes todavía la guía.
No deduzcas funcionalidad interna a partir del diseño.
No inventes nombres de controles que no sean legibles.

Formato de salida:
{
  "screen_name": "...",
  "visible_elements": ["..."],
  "supported_actions": ["..."],
  "uncertainties": ["..."]
}

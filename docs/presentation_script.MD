# Guión para la Exposición del Proyecto Capstone (Máx. 5 minutos)

Este guión está estructurado para cubrir todos los puntos clave de evaluación de la rúbrica de Kaggle: planteamiento del problema, explicación de agentes, arquitectura técnica, demostración en vivo (sincronización con Google Calendar) y pair programming con **Antigravity**.

---

## Estructura del Video y Tiempos
* **0:00 - 0:45 (45s)**: Introducción y Planteamiento del Problema
* **0:45 - 1:30 (45s)**: Explicación de la Solución (Agente Concierge)
* **1:30 - 2:30 (60s)**: Arquitectura Técnica y Conceptos Clave del Curso
* **2:30 - 4:00 (90s)**: Demostración en Vivo (Producción y Local)
* **4:00 - 5:00 (60s)**: El Proceso de Construcción y Conclusión

---

## Guión Paso a Paso

### 1. Introducción y Planteamiento del Problema (0:00 - 0:45)
* **Qué mostrar en pantalla**: Diapositiva del título: *"Goal Planning & Execution Agent"* y luego tu cara o captura de pantalla con los logos de Google Calendar y Gemini.
* **Lo que dices**:
  > *"Hola a todos. Mi nombre es Xaviaerox y hoy les presento el **Goal Planning & Execution Agent**, mi proyecto capstone para el curso Intensive Vibe Coding de Kaggle y Google.*
  > 
  > *El problema que resuelvo es simple pero universal: el **vacío de ejecución**. Todos nos fijamos metas desafiantes como 'Estudiar para la certificación Cisco CyberOps' o 'Aprender Python'. Sin embargo, planificar esas metas en hitos semanales requiere mucho esfuerzo cognitivo. Peor aún, convertir esas listas de tareas en bloques específicos en nuestro calendario diario es tedioso y, al final, las metas se quedan en el papel y nunca se calendarizan para llevarse a cabo."*

### 2. La Solución: The Planning Concierge (0:45 - 1:30)
* **Qué mostrar en pantalla**: Abre el navegador y muestra la interfaz web corriendo en producción en la URL de Google Cloud Run (`https://goal-breakdown-agent-61703236417.us-central1.run.app/`).
* **Lo que dices**:
  > *"Para resolver esto, diseñé un **Agente Concierge** inteligente y seguro. El usuario simplemente introduce su meta, su fecha límite de finalización, sus horarios de disponibilidad semanales y sus preferencias de fin de semana.*
  > 
  > *El agente descompone la meta de lenguaje natural en hitos lógicos y tareas semanales, calcula la distribución del tiempo evitando horas empalmadas y, finalmente, utiliza el protocolo **Model Context Protocol (MCP)** para sincronizar automáticamente estas sesiones en el calendario real de Google del usuario. De esta forma, el agente no solo planifica, sino que automatiza la ejecución."*

### 3. Arquitectura Técnica y Conceptos Clave (1:30 - 2:30)
* **Qué mostrar en pantalla**: Muestra el diagrama de arquitectura del archivo `README.md` o una diapositiva del flujo técnico.
* **Lo que dices**:
  > *"La arquitectura técnica aplica cinco conceptos clave que aprendimos en el curso:*
  > 
  > 1. * **Guardarraíles de Seguridad**: Antes de llamar a los modelos de lenguaje, el agente valida la entrada contra inyecciones de prompts o contenidos dañinos en [guardrails.py](file:///c:/Users/Xaviaerox/Documents/GitHub/goal-breakdown-agent/security/guardrails.py).*
  > 2. * **Tubería de Agente Componible**: En vez de un solo prompt masivo, el coordinador en [runtime.py](file:///c:/Users/Xaviaerox/Documents/GitHub/goal-breakdown-agent/agent_runtime/runtime.py) descubre y encadena dinámicamente **Habilidades Modulares (Skills)** independientes cargadas desde la carpeta `skills/`.*
  > 3. * **Google-GenAI SDK**: Todo el agente está integrado con el nuevo cliente oficial de Gemini en Python utilizando Gemini 2.5 Flash.*
  > 4. * **Autenticación Segura con Google OAuth 2.0**: Para que sea una aplicación SaaS real y multiusuario, implementamos el flujo oficial de consentimiento de Google OAuth 2.0. Cualquier usuario del mundo puede iniciar sesión de forma segura y autorizar de manera temporal la escritura en su calendario.*
  > 5. * **Sincronización Directa de Calendario y Control de Zona Horaria**: El backend en [app.py](file:///c:/Users/Xaviaerox/Documents/GitHub/goal-breakdown-agent/app.py) recibe dinámicamente la zona horaria del navegador del usuario. Esto permite calcular y sincronizar las sesiones directamente mediante la API de Google Calendar usando el token de acceso obtenido, respetando los horarios del usuario al minuto y evitando desfases horarios."*

### 4. Demostración en Vivo (2:30 - 4:00)
* **Qué mostrar en pantalla**: Abre la web en producción, haz clic en **"Iniciar sesión con Google"**, selecciona tu cuenta personal, muestra el estado verde "Conectado". Escribe una meta como: *"Estudiar el curso oficial de Cisco NetAcad CyberOps Associate"*, pon fecha límite, selecciona tus horarios, haz clic en **"Generate & Sync Plan"**. Muestra el panel con los logs y trazas de ejecución en la pestaña de la UI, y luego cambia de pestaña a tu **Google Calendar** para mostrar los eventos recién creados.
* **Lo que dices**:
  > *"Hagamos una prueba en vivo. Primero, inicio sesión de forma segura con mi cuenta de Google. Verán que el panel cambia a verde con mi correo personal 'Conectado'. Ahora escribo mi meta: 'Estudiar el curso oficial de Cisco CyberOps Associate'. Configuro terminar para el 15 de septiembre, disponibilidad de lunes a viernes de 20:00 a 21:30 y sábados por la mañana.*
  > 
  > *Hago clic en 'Generate & Sync Plan'. En segundos, el agente invoca los skills de análisis, hitos y estimación de tiempo. Observen el panel: la traza muestra un puntaje de evaluación del 100%, validando que el plan cumple con todas las métricas de calidad y seguridad. Y si abrimos mi Google Calendar... ¡aquí están! Todos los bloques de estudio están perfectamente creados y sincronizados en tiempo real en mi calendario personal de Google, respetando mi zona horaria exacta."*

### 5. El Proceso de Construcción y Conclusión (4:00 - 5:00)
* **Qué mostrar en pantalla**: Muestra tu editor de código VS Code o tu repositorio de GitHub `xaviaerox/goal-breakdown-agent`.
* **Lo que dices**:
  > *"Construir esto fue una experiencia increíble de vibe coding. Desarrollé el proyecto completo en pair programming con **Antigravity**, el asistente de IA de Google DeepMind integrado directamente en mi IDE. Antigravity me ayudó a modularizar los skills, diseñar las regex de parseo de fechas y depurar el flujo de redirecciones OAuth seguras y los unit tests de la aplicación.*
  > 
  > *El proyecto cuenta con una suite de pruebas automatizada con pytest y un script de evaluación que pasa el 100% de los escenarios de prueba. Este agente representa el asistente de productividad del futuro: autónomo, seguro, respetuoso con las restricciones de tiempo y completamente desplegado en la nube.*
  > 
  > *Muchas gracias por su atención. ¡Espero que les haya gustado!"*

---

## Consejos Finales para la Grabación
1. **Calidad de Audio**: Asegúrate de grabar en un lugar silencioso; el audio claro es fundamental para los puntos de Kaggle.
2. **Fluidez**: No te preocupes por hablar rápido, lo importante es mostrar la interfaz funcionando y los eventos creados en Google Calendar en tiempo real.
3. **Subtítulos**: Si puedes, agrega subtítulos automáticos en YouTube para que los evaluadores de Kaggle (que suelen ser angloparlantes) puedan seguir tu presentación en español sin problemas.

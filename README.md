# Teclado Ocular Binario (PySide6)

## Ejecutar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Opciones:

```bash
python main.py --fullscreen
python main.py --config /ruta/a/settings.yml
```

## Configuracion

El archivo se crea en:
- Windows: `%APPDATA%/InvoaKeyboard/settings.yml`
- macOS: `~/Library/Application Support/InvoaKeyboard/settings.yml`
- Linux: `~/.config/InvoaKeyboard/settings.yml`

Formato soportado en runtime: **YAML**.

Ejemplo (`settings.yml` con comentarios en español):

```yaml
# Version del esquema de configuracion para futuras migraciones
config_version: 1

app:
  # Distribucion de letras (hoy: A-Z)
  layout: "A-Z"

interaction:
  # Tiempo (ms) para considerar click largo (deshacer)
  long_click_ms: 2000
  # Habilita deshacer con click largo
  undo_on_long_click: true
  # Limite minimo permitido para click largo
  min_long_click_ms: 500
  # Limite maximo permitido para click largo
  max_long_click_ms: 5000

ui:
  # Escala general de texto y controles
  font_scale: 1.0
  # Muestra la tira del alfabeto resaltada
  show_alphabet_strip: true
  show_actions:
    # Mostrar boton borrar ultimo caracter
    backspace: true
    # Mostrar boton enviar al sistema
    send: true
    # Mostrar boton de voz (TTS)
    speak: true
```

Notas de validacion:
- `interaction.long_click_ms` se limita entre `min_long_click_ms` y `max_long_click_ms`.
- `ui.font_scale` se limita entre `0.5` y `2.5`.
- `window.on_top_refresh_ms` se limita a un minimo de `250`.
- Colores invalidos vuelven al valor por defecto.
- Si el YAML es invalido, se regeneran valores por defecto.

La primera vez se genera una plantilla completa comentada automaticamente.

## Notas de permisos

- En macOS, habilitar permisos de Accesibilidad para que la app pueda escribir.
- En Windows, puede requerir ejecutar como administrador dependiendo del entorno.

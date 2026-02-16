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
python main.py --config /ruta/a/settings.json
```

## Configuracion

El archivo se crea en:
- Windows: `%APPDATA%/InvoaKeyboard/settings.json`
- macOS: `~/Library/Application Support/InvoaKeyboard/settings.json`
- Linux: `~/.config/InvoaKeyboard/settings.json`

Ejemplo:

```json
{
  "long_click_ms": 2000,
  "font_scale": 1.0,
  "colors": {
    "bg": "#000000",
    "fg": "#FFFFFF",
    "hover": "#333333"
  },
  "layout": "A-Z",
  "output_mode": "global"
}
```

## Notas de permisos

- En macOS, habilitar permisos de Accesibilidad para que la app pueda escribir.
- En Windows, puede requerir ejecutar como administrador dependiendo del entorno.

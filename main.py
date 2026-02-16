from __future__ import annotations

import argparse

from invoa_keyboard.app import run_app
from invoa_keyboard.settings import load_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Teclado ocular binario accesible")
    parser.add_argument("--config", help="Ruta a settings.json personalizado")
    parser.add_argument("--fullscreen", action="store_true", help="Abrir en pantalla completa")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = load_settings(args.config)
    return run_app(settings, args.fullscreen)


if __name__ == "__main__":
    raise SystemExit(main())

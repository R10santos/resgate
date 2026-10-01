"""Entrada da campanha ECO-7 e diagnósticos de execução."""
import argparse
import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


def main():
    parser = argparse.ArgumentParser(description="ECO-7 · Protocolo Aurora")
    parser.add_argument("--frames", type=int, help="Encerra após N quadros (diagnóstico).")
    parser.add_argument("--screenshot", help="Salva a tela ao encerrar o diagnóstico.")
    parser.add_argument("--headless", action="store_true", help="Drivers virtuais para testes.")
    parser.add_argument("--preview-chapter", type=int, choices=range(1, 6), help="Prévia de capítulo sem alterar o save.")
    args = parser.parse_args()
    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    from src.echo.app import Game
    game = Game(allow_save=not bool(args.preview_chapter))
    if args.preview_chapter:
        game.load(dict(chapter=args.preview_chapter - 1, flags={}, logs=[]), intro=False, persist=False)
    game.run(args.frames, args.screenshot)


if __name__ == "__main__":
    main()

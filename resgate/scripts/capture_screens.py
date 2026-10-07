"""Prévias visuais configuradas para revisão; não são uma partida completa."""
import os
import sys
from pathlib import Path
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from src.echo.app import Game
from src.echo.model import at
from src.echo.story import LOGS


def main():
    output = Path('docs/eco7')
    output.mkdir(parents=True, exist_ok=True)
    g = Game(allow_save=False)
    def capture(name):
        g.draw()
        pygame.image.save(g.screen, str(output / (name + '.png')))
    capture('01-menu')
    for chapter in range(5):
        g.load(dict(chapter=chapter, flags={'protocol': 'preserve'}, logs=[]), intro=False, persist=False)
        w = g.world
        w.player = at(*[(5, 17), (7, 17), (17, 5), (26, 17), (8, 5)][chapter])
        if chapter == 1:
            w.join('IVO', w.node('ivo'))
        elif chapter == 3:
            for n in w.nodes:
                if n.id.startswith('seal'):
                    n.done = True
            next(e for e in w.enemies if e.kind == 'boss').active = True
        elif chapter == 4:
            w.node('stabilizer').done = True
            w.join('NINA', w.node('nina'))
            w.timer = 180
        capture(f'fase-{chapter+1}')
    g.load(dict(chapter=2, flags={}, logs=[]), persist=False)
    capture('dialogo')
    for state, name in [('choice', 'escolha'), ('journal', 'diario'), ('help', 'controles'), ('difficulty', 'dificuldade'), ('upgrade', 'melhorias'), ('map', 'mapa')]:
        g.state = state
        g.world.logs = list(LOGS)
        capture(name)
    pygame.quit()


if __name__ == '__main__':
    main()

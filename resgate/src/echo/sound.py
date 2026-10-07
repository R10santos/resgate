"""Áudio sintetizado original. Funciona também sem dispositivo de áudio."""
from array import array
import math
import random
import pygame


class Sound:
    def __init__(self):
        self._muted = False
        self.ambient_channel = None
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            rate, _, channels = pygame.mixer.get_init()
            rng = random.Random(7)
            for name, freq, duration in [('shoot', 620, .075), ('hit', 95, .18), ('dash', 320, .12),
                                         ('emp', 150, .38), ('heal', 780, .25), ('interact', 1060, .09), ('scatter', 180, .19)]:
                samples = array('h')
                for i in range(int(rate * duration)):
                    f = i / (rate * duration)
                    wave = math.sin(math.tau * freq * (1 - f * .5) * i / rate)
                    if name in ('shoot', 'hit', 'emp'):
                        wave = wave * .7 + rng.uniform(-1, 1) * .3
                    samples.extend([int(4100 * wave * (1 - f))] * channels)
                self.sounds[name] = pygame.mixer.Sound(buffer=samples)
            # Ciclo de quatro segundos, com frequências fechando no mesmo período.
            bed = array('h')
            for i in range(rate * 4):
                t = i / rate
                swell = .65 + .35 * math.sin(math.tau * t / 4)
                wave = (math.sin(math.tau * 55 * t) * .48 + math.sin(math.tau * 82.5 * t) * .22
                        + math.sin(math.tau * 110 * t) * .12 + math.sin(math.tau * 130.75 * t) * .08)
                bed.extend([int(1100 * swell * wave)] * channels)
            self.ambient = pygame.mixer.Sound(buffer=bed)
            self.ambient_channel = self.ambient.play(loops=-1)
            if self.ambient_channel:
                self.ambient_channel.set_volume(.5)
        except pygame.error:
            pass

    @property
    def muted(self):
        return self._muted

    @muted.setter
    def muted(self, value):
        self._muted = bool(value)
        if self.ambient_channel:
            self.ambient_channel.set_volume(0 if value else .5)

    def play(self, name):
        if not self.muted and name in self.sounds:
            self.sounds[name].play()

"""The galaxy medal: a gold star disk on a ribbon (warp cut-scene, title, star map)."""
import math

import pygame

from ..config.palette import COIN

RIBBON = ((130, 240, 90), (40, 120, 40))        # galaxy 1: SWARMBANE green


def draw_medal(surf, x, y, time, scale=1):
    """Medal centred on (x, y); scale 1 = 15 px disk, 2 = 30 px. It glints now and then."""
    x, y = int(x), int(y)
    r = 7 * scale
    light, dark = RIBBON
    for side in (-1, 1):                         # the ribbon: two tails above the disk
        points = [(x + side * 2 * scale, y - r + scale), (x + side * 6 * scale, y - r - 9 * scale),
                  (x + side * 2 * scale, y - r - 9 * scale), (x - side * scale, y - r)]
        pygame.draw.polygon(surf, dark if side < 0 else light, points)
    pygame.draw.circle(surf, (40, 26, 8), (x, y), r + 1)
    pygame.draw.circle(surf, COIN[3], (x, y), r)
    pygame.draw.circle(surf, COIN[2], (x, y), r - scale)
    star = []
    for i in range(10):                          # a five-pointed star
        a = -math.pi / 2 + i * math.pi / 5
        d = (r - 2 * scale) if i % 2 == 0 else (r - 2 * scale) * 0.45
        star.append((x + math.cos(a) * d, y + math.sin(a) * d))
    pygame.draw.polygon(surf, COIN[1], star)
    glint = (time * 0.7) % 3.0
    if glint < 0.4:                              # a glint sweeps over it
        gx = x - r + int(glint / 0.4 * 2 * r)
        pygame.draw.line(surf, (255, 255, 255), (gx, y - r // 2), (gx + scale, y - r // 2 - scale))
        surf.fill((255, 255, 255), (gx, y - r // 2, scale, scale))

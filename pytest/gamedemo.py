#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" based on example 2 from thepythongamebook.com
"""

from __future__ import print_function, division
import pygame, sys, signal

def cleanup(signum, frame):
	global mainloop

	mainloop = False

signal.signal(signal.SIGUSR1, cleanup)

pygame.init()
font = pygame.font.SysFont('mono', 20, bold=True)
ident = font.render(sys.argv[1], True, (25,0,0))

screen = pygame.display.set_mode((800,480), pygame.FULLSCREEN | pygame.DOUBLEBUF)
background = pygame.Surface(screen.get_size())
background.fill((255,255,255))
background = background.convert()
background.blit(ident, (400, 300))
screen.blit(background, (0,0))
clock = pygame.time.Clock()

mainloop = True
FPS = 30
playtime = 0.0

while mainloop:
	milliseconds = clock.tick(FPS)
	playtime += milliseconds / 1000.0

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			mainloop = False
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_ESCAPE:
				mainloop = False
	text = "FPS: {0:.2f}  Playtime: {1:.2f}".format(clock.get_fps(), playtime)
	pygame.display.set_caption(text)
	surface = font.render(text, True, (0,255,0))
	screen.blit(background, (0,0))
	screen.blit(surface, (300, 150))


	pygame.display.flip()

pygame.quit()

print("This game was played for {0:.2f} seconds".format(playtime))

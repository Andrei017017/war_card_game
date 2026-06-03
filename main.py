from pathlib import Path
import pygame
from logic import Logic, Card
from phase_manager import PhaseManager
from game_state import GameState
from animation import Animation
from utils import display_fps, cards_left

image_dir = Path(__file__).parent / 'images'
bg = image_dir / 'bg_640x480.jpg'
cb = image_dir / 'cb.png'

#sound_dir = Path(__file__).parent / 'sounds'
#deal_sound = pygame.mixer.Sound(str(sound_dir / 'Dealing-cards-sound-[AudioTrimmer.com].mp3'))

pygame.init()
#pygame.mixer.init()

SCREEN = pygame.display.set_mode((640, 480))
UI_TEXT = {
    'fps': [pygame.font.SysFont("Arial.ttf", 18), pygame.Color("coral")],
    'card_counter': [pygame.font.SysFont("Arial.ttf", 30), pygame.Color("white")],
    'result': [pygame.font.SysFont('Arial.ttf', 30), pygame.Color("purple")]
}
BACKGROUND = pygame.image.load(bg).convert()
CARD_BACK = pygame.image.load(cb).convert()

pygame.display.set_caption("WAR Card Game")
clock = pygame.time.Clock()

POSITIONS = {
    'start':        pygame.Vector2(45, 58),
    'center':       pygame.Vector2(320, 138),
    'player_hand':  pygame.Vector2(220, 338),
    'ai_hand':      pygame.Vector2(420, 338),
    'player_battle':pygame.Vector2(220, 138),
    'player_war':   pygame.Vector2(68, 138),
    'ai_battle':    pygame.Vector2(420, 138),
    'ai_war':       pygame.Vector2(572, 138)
}

logic = Logic()

rank_order, deck = logic.make_deck(Card.all_sprites)
game_state = GameState(rank_order, deck)

animation = Animation(Card.all_sprites)
phases = PhaseManager(game_state, animation, logic, POSITIONS, UI_TEXT)

running = True

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False  # Example: Exit the loop
            else:
                phases.key_pressed = True

    dt = clock.tick(60) / 1000.0  # real frame time

    phases.tick()

    SCREEN.blit(BACKGROUND, (0, 0))
    Card.all_sprites.update()
    Card.all_sprites.draw(SCREEN)

    for text, pos in cards_left(UI_TEXT, phases.game_state, POSITIONS):
        SCREEN.blit(text, pos)

    for surf, rect in phases.active_ui:
        SCREEN.blit(surf, rect)
    SCREEN.blit(display_fps(UI_TEXT, clock), (590, 10))

    pygame.display.update()
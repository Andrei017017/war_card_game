import pygame
import math
from pathlib import Path
from utils import display_fps

from itertools import zip_longest

class Animation():
    def __init__(self, all_sprites):
        self.all_sprites = all_sprites
        self.step = 10
        self.cycles = 1.0
        self.scaling_gen = None
        self._award_stack = None

    def start_deck(self, game_state, POSITIONS):
        all_arrived = True

        for card in game_state.deck:
            card.flipped = False
            card.pos.move_towards_ip(POSITIONS['start'], self.step)
            if card.pos != POSITIONS['start']:
                all_arrived = False

        return all_arrived

    def move_deck(self, game_state, POSITIONS):
        all_arrived = True
        
        for i, card in enumerate(game_state.deck[:int(self.cycles)]):

            if card._layer < 0:
                card._layer = i + 1
                self.all_sprites.change_layer(card, card._layer)

            card.pos.move_towards_ip(POSITIONS['center'], self.step)
            if card.pos != POSITIONS['center']:
                all_arrived = False

        self.cycles += 0.1

        if all_arrived:
            self.cycles = 1

        return all_arrived

    def split_deck(self, game_state, POSITIONS):
        all_arrived = True
        for card in game_state.player_hand:
            card.pos.move_towards_ip(POSITIONS['player_hand'], self.step)
            if card.pos != POSITIONS['player_hand']:
                all_arrived = False
        for card in game_state.ai_hand:
            card.pos.move_towards_ip(POSITIONS['ai_hand'], self.step)
            if card.pos != POSITIONS['ai_hand']:
                all_arrived = False

        return all_arrived
    
    def start_battle(self, game_state, POSITIONS):
        all_arrived = True

        player_card, ai_card = game_state.player_battle[-1], game_state.ai_battle[-1]

        player_card.pos.move_towards_ip(POSITIONS['player_battle'], self.step)
        ai_card.pos.move_towards_ip(POSITIONS['ai_battle'], self.step)

        if player_card.pos != POSITIONS['player_battle']:
            return False

        player_card.flipped = ai_card.flipped = True

        return all_arrived
    
    def start_war(self, game_state, POSITIONS):
        all_arrived = True
        '''    
        old player battle card    - now: game_state.player_war[-2].    Moves to POSITIONS['player_war']
        new player war card       - now: game_state.player_war[-1].    Moves to POSITIONS['player_war']
        new player battle card    - now: game_state.player_battle[-1]. Moves to POSITIONS['player_battle']
        '''
        game_state.player_war[-2].flipped = game_state.ai_war[-2].flipped = False 

        game_state.player_war[-2].pos.move_towards_ip(POSITIONS['player_war'], self.step)
        game_state.player_war[-1].pos.move_towards_ip(POSITIONS['player_war'], self.step)
        game_state.player_battle[-1].pos.move_towards_ip(POSITIONS['player_battle'], self.step)

        game_state.ai_war[-2].pos.move_towards_ip(POSITIONS['ai_war'], self.step)
        game_state.ai_war[-1].pos.move_towards_ip(POSITIONS['ai_war'], self.step)
        game_state.ai_battle[-1].pos.move_towards_ip(POSITIONS['ai_battle'], self.step)

        if game_state.player_battle[-1].pos != POSITIONS['player_battle']:
            return False
        else:
            game_state.player_battle[-1].flipped = game_state.ai_battle[-1].flipped = True

        if game_state.player_war[-1].pos != POSITIONS['player_war']:
            all_arrived = False

        return all_arrived
    
    def scale_card(self, game_state):
        if not self.scaling_gen:
            def scaling_generator(frames=20, peak=0.3):
                for i in range(frames):
                    progress = i / (frames - 1)
                    yield 1.0 + peak * math.sin(progress * math.pi)  # 1.0 → 1.3 → 1.0

            self.scaling_gen = scaling_generator()
            # Cache originals to prevent quality degradation
            self._orig_player = game_state.player_battle[-1].image.copy()
            self._orig_ai = game_state.ai_battle[-1].image.copy()

        try:
            scale_factor = next(self.scaling_gen)
            player_card, ai_card = game_state.player_battle[-1], game_state.ai_battle[-1]
            player_card._skip_update = True
            ai_card._skip_update = True

            # scale_by returns a NEW surface. Must assign it.
            if game_state.winner == 'player':
                player_card.image = pygame.transform.scale_by(self._orig_player, scale_factor)
            elif game_state.winner == 'ai':
                ai_card.image = pygame.transform.scale_by(self._orig_ai, scale_factor)
            else:
                player_card.image = pygame.transform.scale_by(self._orig_player, scale_factor)
                ai_card.image = pygame.transform.scale_by(self._orig_ai, scale_factor)

            # Lock rects to your center positions
            player_card.rect = player_card.image.get_rect(center=player_card.pos)
            ai_card.rect = ai_card.image.get_rect(center=ai_card.pos)

            return False  # Still animating

        except StopIteration:
            # Restore exact originals when generator exhausts
            game_state.player_battle[-1].image = self._orig_player
            game_state.ai_battle[-1].image = self._orig_ai
            del game_state.player_battle[-1]._skip_update
            del game_state.ai_battle[-1]._skip_update
            
            self.scaling_gen = None
            self._orig_player = None
            self._orig_ai = None
            return True  # Animation finished

    def award_cards(self, game_state, POSITIONS):
        winner_hand = POSITIONS['player_hand'] if game_state.winner == 'player' else POSITIONS['ai_hand']

        # 1. Build the interleaved stack ONCE per phase
        if self._award_stack is None:
            self._award_stack = [
                card for group in zip_longest(
                    game_state.player_battle,
                    game_state.ai_battle,
                    game_state.player_war,
                    game_state.ai_war
                )
                for card in group if card is not None
            ]
            self.cycles = 1.0  # Reset timer for this new phase

        self.cycles += 0.1  
        limit = int(self.cycles)

        all_arrived = True

        # 3. Move only the cards up to the current limit
        for card in self._award_stack[:limit]:
            card.flipped = False
            card.pos.move_towards_ip(winner_hand, self.step)
            
            if card.pos != winner_hand:
                all_arrived = False

        # 4. Check completion: All cards released AND all have arrived
        if limit >= len(self._award_stack) and all_arrived:
            self._award_stack = None  # Clean up cache for the next battle
            return True  # Animation done, switch phase

        return False  # Still animating


if __name__ == '__main__':

    image_dir = Path(__file__).parent / 'images'
    bg = image_dir / 'bg_640x480.jpg'
    cb = image_dir / 'cb.png'

    pygame.init()

    SCREEN = pygame.display.set_mode((640, 480))
    FONT = pygame.font.SysFont("Arial.ttf", 18)
    COLOR = pygame.Color("coral")
    BACKGROUND = pygame.image.load(bg).convert()
    CARD_BACK = pygame.image.load(cb).convert()

    POSITIONS = {
        'start':        pygame.Vector2(10, 10),
        'center':       pygame.Vector2(285, 90),
        'left_pile':    pygame.Vector2(185, 290),
        'right_pile':   pygame.Vector2(385, 290),
        'player_battle':pygame.Vector2(185, 90),
        'player_war':   pygame.Vector2(33, 90),
        'ai_battle':    pygame.Vector2(385, 90),
        'ai_war':       pygame.Vector2(537, 90)
    }
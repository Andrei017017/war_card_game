import random
import pygame
from collections import deque
from pathlib import Path

image_dir = Path(__file__).parent / 'images'

pygame.init()

SCREEN = pygame.display.set_mode((640, 480))

class Card(pygame.sprite.Sprite):

    all_sprites = pygame.sprite.LayeredUpdates()

    def __init__(self, rank, suit):
        super().__init__()
        self.rank = rank
        self.suit = suit
        self.file_name = image_dir / f'{self.rank}{self.suit}.png'
        self.cb_name = image_dir / 'cb.png'
        self.flipped = False

        self.image_back = pygame.image.load(image_dir / 'cb.png').convert()
        self.image_face = pygame.image.load(image_dir / f'{self.rank}{self.suit}.png').convert()
        self.image = self.image_back
        self.pos = pygame.Vector2(45, 57).copy()
        self.rect = self.image.get_rect(center=self.pos)
        self._layer = 0

        Card.all_sprites.add(self, layer = self.layer)

    def __str__(self):
        return f'{self.rank}{self.suit} at {tuple(self.pos)}'

    def update(self):
        if getattr(self, '_skip_update', False):  # Bypass only when flag exists
            return
        self.image = self.image_face if self.flipped else self.image_back
        self.rect = self.image.get_rect(center=self.pos)

class Logic():
    def __init__(self):
        self.done = False

    def make_deck(self, all_sprites):

        if all_sprites:
            all_sprites.empty()

        ranks = ['J', 'Q', 'K']
        suits = ['c', 'd', 'h', 's']
        rank_order = {rank: i for i, rank in enumerate(ranks)}

        deck = [Card(rank, suit) for rank in ranks for suit in suits]

        random.shuffle(deck)

        for _layer, card in enumerate(deck, 1):
            card._layer = -_layer
            all_sprites.change_layer(card, card._layer)

        return rank_order, deck
    
    def ready_deck(self, game_state):
        all_cards = (
            list(game_state.player_hand) +
            list(game_state.ai_hand) +
            game_state.player_battle +
            game_state.ai_battle +
            game_state.player_war +
            game_state.ai_war
        )
    
        game_state.deck = all_cards
        game_state.player_hand.clear()
        game_state.ai_hand.clear()

    def split_deck(self, game_state):
        player_hand = []
        ai_hand = []
        
        for i, card in enumerate(game_state.deck):
            if i % 2:
                player_hand.append(card)
            else:
                ai_hand.append(card)
        
        game_state.player_hand = deque(player_hand)
        game_state.ai_hand = deque(ai_hand)
        game_state.deck = []  # Clear the deck
        self.done = True
    
    # called by game director, when: 1) war = False; 2) player_stack and ai_stack are empty; 1 card played by each player
    def start_battle(self, game_state):
        game_state.player_battle = [game_state.player_hand.pop()]
        game_state.ai_battle = [game_state.ai_hand.pop()]
        self.done = True

    
    def start_war(self, game_state):
        # Check for enough cards first
        # Handle insufficient cards - player with more wins
        if game_state.player_cards_left < 2:
            return 'ai'
        elif game_state.ai_cards_left < 2:
            return 'player'
            
        # moving previous battle card to war stack
        old_player_battle = game_state.player_battle.pop()
        old_player_battle.flipped = False
        game_state.player_war.append(old_player_battle)

        old_ai_battle = game_state.ai_battle.pop()
        old_ai_battle.flipped = False
        game_state.ai_war.append(old_ai_battle)

        # dealing new war + battle card as before
        game_state.player_war.append(game_state.player_hand.pop())
        game_state.player_battle.append(game_state.player_hand.pop())
        game_state.ai_war.append(game_state.ai_hand.pop())
        game_state.ai_battle.append(game_state.ai_hand.pop())

    def evaluate_battle(self, game_state):
        player_card = game_state.player_battle[-1]
        ai_card = game_state.ai_battle[-1]
        
        if game_state.rank_order[player_card.rank] > game_state.rank_order[ai_card.rank]:
            game_state.winner = 'player'
            game_state.war = False
        elif game_state.rank_order[player_card.rank] < game_state.rank_order[ai_card.rank]:
            game_state.winner = 'ai'
            game_state.war = False
        else:
            game_state.winner = None
            game_state.war = True

    def award_cards(self, game_state):
        
        combined_stack = (
            game_state.player_battle + 
            game_state.ai_battle +
            game_state.player_war +
            game_state.ai_war
        )

        if game_state.winner == 'player':
            game_state.player_hand.extendleft(combined_stack)
        elif game_state.winner == 'ai':
            game_state.ai_hand.extendleft(combined_stack)

        if len(game_state.player_hand) == 0:
            return 'ai'
        elif len(game_state.ai_hand) == 0:
            return 'player'
        
        game_state.winner = None
        game_state.player_battle = []
        game_state.player_war = []
        game_state.ai_battle = []
        game_state.ai_war = []
        game_state.war = False
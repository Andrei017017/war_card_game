from collections import deque

class GameState:
    def __init__(self, rank_order, deck):
        self.rank_order: dict = rank_order
        self.deck: list = deck
        self.player_hand: deque = deque()
        self.ai_hand: deque = deque()
        self.player_battle: list = []
        self.ai_battle: list = []
        self.player_war: list = []
        self.ai_war: list = []
        self.war: bool = False
        self.winner: str = None

    @property
    def player_cards_left(self):
        return len(self.player_hand)
    
    @property
    def ai_cards_left(self):
        return len(self.ai_hand)
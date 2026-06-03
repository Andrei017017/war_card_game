import pygame
from game_state import GameState
from logic import Card

class PhaseManager():
    def __init__(self, game_state, animation, logic, POSITIONS, UI_TEXT):
        self.game_state = game_state
        self.animation = animation
        self.logic = logic
        self.POSITIONS = POSITIONS
        self.UI_TEXT = UI_TEXT
        self.active_ui = []
        self.key_pressed = False
        self.current = 'start_game'

        self._phases = {
            'start_game': self._phase_start_game,
            'anim_move_deck': self._phase_anim_move_deck,
            'logic_split': self._phase_logic_split,
            'anim_split': self._phase_anim_split,
            'logic_start_battle': self._phase_logic_start_battle,
            'anim_start_battle': self._phase_anim_start_battle,
            'logic_eval_battle': self._phase_logic_eval_battle,
            'logic_start_war': self._phase_logic_start_war,
            'logic_award_cards': self._phase_logic_award_cards,
            'anim_award_cards': self._phase_anim_award_cards,
            'anim_start_war': self._phase_anim_start_war,
            'anim_scale_card': self._phase_anim_scale_card,            
            'universal_show_result': self._phase_universal_show_result,
            'check_game_over': self._phase_check_game_over,
            'game_over': self._phase_game_over,
            'logic_ready_deck': self._phase_logic_ready_deck,
            'anim_start_deck': self._phase_anim_start_deck,
            'reset': self._phase_reset 
        }

    def tick(self):
        self._phases[self.current]()

    def _phase_logic_ready_deck(self):
        self.logic.ready_deck(self.game_state)
        self.current = 'anim_start_deck'

    def _phase_anim_start_deck(self):
        if self.animation.start_deck(self.game_state, self.POSITIONS):
            self.key_pressed = False
            self.current = 'reset'

    def _phase_reset(self):
        # 1. Clear Sprites
        Card.all_sprites.empty()
        
        # 2. Re-run setup logic on existing objects
        rank_order, deck = self.logic.make_deck(Card.all_sprites)
        
        # 3. Reset Game State
        self.game_state = GameState(rank_order, deck)
        
        # 4. Reset Animation trackers
        self.animation.cycles = 1.0
        self.animation.award_stack = None
        self.animation.scaling_gen = None
        
        self.current = 'start_game'


    def _phase_start_game(self):
        if self.key_pressed:
            self.current = 'anim_move_deck'

    def _phase_anim_move_deck(self):
        if self.animation.move_deck(self.game_state, self.POSITIONS):
            self.current = 'logic_split'

    def _phase_logic_split(self):
        self.logic.split_deck(self.game_state)
        self.current = 'anim_split'

    def _phase_anim_split(self):
        if self.animation.split_deck(self.game_state, self.POSITIONS):
            self.key_pressed = False
            self.current = 'logic_start_battle'

    def _phase_logic_start_battle(self):
        if self.key_pressed:
            self.logic.start_battle(self.game_state)
            self.current = 'anim_start_battle'

    def _phase_anim_start_battle(self):       
        if self.animation.start_battle(self.game_state, self.POSITIONS):
            self.key_pressed = False
            self.current = 'logic_eval_battle'
            
    def _phase_logic_eval_battle(self):
        self.logic.evaluate_battle(self.game_state)
        self.current = 'anim_scale_card'

    def _phase_universal_show_result(self):
        if not self.active_ui:
            if self.game_state.war:
                result_pos = pygame.Vector2(320, 138)
                result_text = 'WAR'
            else:
                result_pos = self.POSITIONS['player_battle'] if self.game_state.winner == 'player' else self.POSITIONS['ai_battle']
                result_text = 'WINNER'

            font, color = self.UI_TEXT['result']
            surf = font.render(result_text, True, color)
            result_pos = result_pos - (0, 95)
            rect = surf.get_rect(center=result_pos)
            self.active_ui.append((surf, rect))

        if self.key_pressed:
            self.active_ui = []
            if self.game_state.war:
                self.current = 'check_game_over'
            else:
                self.current = 'anim_award_cards'

    def _phase_logic_start_war(self):
        if self.key_pressed:
            self.logic.start_war(self.game_state)
            self.current = 'anim_start_war'

    def _phase_anim_start_war(self):
        if self.animation.start_war(self.game_state, self.POSITIONS):
            self.key_pressed = False
            self.current = 'logic_eval_battle'

    def _phase_anim_scale_card(self):
        if self.animation.scale_card(self.game_state):
            self.current = 'universal_show_result'

    def _phase_logic_award_cards(self):
        self.logic.award_cards(self.game_state)
        self.current = 'check_game_over'

    def _phase_anim_award_cards(self):
        if self.animation.award_cards(self.game_state, self.POSITIONS):
            self.key_pressed = False
            self.current = 'logic_award_cards'

    def _phase_check_game_over(self):
        # Not enough cards in hand for battle
        if len(self.game_state.player_hand) == 0 or len(self.game_state.ai_hand) == 0:
            self.current = 'game_over'
            return

        # Not enough cards in hand for war
        if self.game_state.war:
            if len(self.game_state.player_hand) < 2 or len(self.game_state.ai_hand) < 2:
                self.current = 'game_over'
                return
            else:
                self.current = 'logic_start_war'
                return

        self.current = 'logic_start_battle'

    def _phase_game_over(self):

        if not self.active_ui:
            winner_text = "YOU WIN!" if len(self.game_state.ai_hand) == 0 else "YOU LOSE!"
            winner_text += '\nPress R to Restart'

            font, color = self.UI_TEXT['result']
            result_pos = self.POSITIONS['center'] - (0, 95)
            
            surf = font.render(winner_text, True, color)
            rect = surf.get_rect(center=result_pos)
            
            self.active_ui.append((surf, rect))

        # Wait for restart key
        if self.key_pressed and pygame.key.get_pressed()[pygame.K_r]:
            self.active_ui = []
            self.current = 'logic_ready_deck' 




def display_fps(UI_TEXT, clock):

    fps = str(int(clock.get_fps()))
    font, color = UI_TEXT['fps']
    fps_text = font.render(f"FPS: {fps}", True, color)
    
    return fps_text

def cards_left(UI_TEXT, game_state, POSITIONS):
    font, color = UI_TEXT['card_counter']
    
    player_cards = len(game_state.player_hand)
    ai_cards = len(game_state.ai_hand)
    player_surf = font.render(str(player_cards), True, color)
    ai_surf = font.render(str(ai_cards), True, color)
    player_pos = POSITIONS['player_hand'] + (-5, 72)
    ai_pos = POSITIONS['ai_hand'] + (-5, 72)
    
    return (player_surf, player_pos), (ai_surf, ai_pos)
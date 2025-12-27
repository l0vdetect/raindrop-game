cd ~/rainstream/raindrop-game

# Create the file directly
cat > raindrop_game.py << 'EOF'
#!/usr/bin/env python3
"""
Raindrop Game - Pattern Recognition Challenge
"""
import pygame
import random
import sys
from enum import Enum

pygame.init()

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)
GREEN = (50, 255, 50)
RED = (255, 50, 50)
CYAN = (50, 200, 200)
DARK_GRAY = (40, 40, 40)

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3

class RaindropGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Raindrop Game")
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.Font(None, 48)
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 24)
        
        self.state = GameState.MENU
        self.running = True
        self.reset_game()
    
    def reset_game(self):
        self.score = 0
        self.combo = 0
        self.drops = []
        self.time_remaining = 120
        self.frame_count = 0
        self.player_x = SCREEN_WIDTH // 2
        self.player_y = SCREEN_HEIGHT - 60
    
    def spawn_raindrop(self):
        if self.frame_count % 10 == 0:
            x = random.randint(20, SCREEN_WIDTH - 20)
            y = -20
            speed = 4
            size = random.randint(8, 15)
            self.drops.append({'x': x, 'y': y, 'speed': speed, 'size': size})
    
    def update_drops(self):
        for drop in self.drops[:]:
            drop['y'] += drop['speed']
            if drop['y'] > SCREEN_HEIGHT:
                self.drops.remove(drop)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU
                    self.reset_game()
                elif event.key == pygame.K_SPACE and self.state == GameState.MENU:
                    self.state = GameState.PLAYING
                elif event.key == pygame.K_SPACE and self.state == GameState.GAME_OVER:
                    self.state = GameState.MENU
                    self.reset_game()
            elif event.type == pygame.MOUSEMOTION:
                self.player_x = event.pos[0]
                self.player_y = event.pos[1]
            elif event.type == pygame.MOUSEBUTTONDOWN and self.state == GameState.PLAYING:
                for drop in self.drops[:]:
                    dx = drop['x'] - event.pos[0]
                    dy = drop['y'] - event.pos[1]
                    distance = (dx**2 + dy**2)**0.5
                    if distance < drop['size'] + 20:
                        self.drops.remove(drop)
                        self.score += 10 + (self.combo * 5)
                        self.combo += 1
    
    def update(self):
        self.frame_count += 1
        if self.state == GameState.PLAYING:
            self.time_remaining = max(0, 120 - (self.frame_count // FPS))
            self.spawn_raindrop()
            self.update_drops()
            if self.time_remaining == 0:
                self.state = GameState.GAME_OVER
    
    def draw_menu(self):
        self.screen.fill(DARK_GRAY)
        title = self.font_title.render("RAINDROP GAME", True, CYAN)
        inst = self.font_medium.render("Click raindrops to score points!", True, WHITE)
        start = self.font_medium.render("Press SPACE to start", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
        self.screen.blit(inst, (SCREEN_WIDTH//2 - inst.get_width()//2, 300))
        self.screen.blit(start, (SCREEN_WIDTH//2 - start.get_width()//2, 400))
    
    def draw_game(self):
        self.screen.fill(BLACK)
        for drop in self.drops:
            pygame.draw.circle(self.screen, BLUE, (int(drop['x']), int(drop['y'])), drop['size'])
        pygame.draw.circle(self.screen, GREEN, (self.player_x, self.player_y), 20)
        
        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        time_text = self.font_medium.render(f"Time: {self.time_remaining}s", True, WHITE)
        combo_text = self.font_medium.render(f"Combo: {self.combo}x", True, GREEN)
        self.screen.blit(score_text, (20, 20))
        self.screen.blit(time_text, (SCREEN_WIDTH - 200, 20))
        self.screen.blit(combo_text, (20, 60))
    
    def draw_game_over(self):
        self.screen.fill(DARK_GRAY)
        game_over = self.font_title.render("GAME OVER", True, RED)
        final = self.font_large.render(f"Final Score: {self.score}", True, WHITE)
        restart = self.font_medium.render("Press SPACE to restart", True, WHITE)
        self.screen.blit(game_over, (SCREEN_WIDTH//2 - game_over.get_width()//2, 150))
        self.screen.blit(final, (SCREEN_WIDTH//2 - final.get_width()//2, 300))
        self.screen.blit(restart, (SCREEN_WIDTH//2 - restart.get_width()//2, 400))
    
    def draw(self):
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING:
            self.draw_game()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = RaindropGame()
    game.run()
EOF
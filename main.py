
import sys, os, math, random, time
import pygame
from pygame import gfxdraw

# ---------------------------------------------
# ITM Snake Game - Snakes & Ladders (1 human + 3 bots)
# Made with ❤️ using Python + pygame
# ---------------------------------------------

TITLE = "ITM Snake Game"
WIDTH, HEIGHT = 1000, 800
FPS = 60

BOARD_SIZE = 10  # 10x10
CELL = 60
MARGIN = 30
SIDEPANEL_W = 300

# Colors
WHITE = (245, 245, 245)
BLACK = (25, 25, 25)
GREY = (70, 70, 70)
LIGHT = (220, 220, 220)
BG = (18, 20, 28)
PRIMARY = (100, 180, 255)
ACCENT = (255, 200, 40)

# Player colors
PLAYER_COLORS = [
    (76, 139, 245),   # human - blue
    (238, 99, 99),    # bot 1 - red
    (70, 207, 123),   # bot 2 - green
    (240, 220, 70),   # bot 3 - yellow
]

# Snakes and Ladders mapping (start -> end)
SNAKES = {
    98: 78,
    95: 75,
    93: 73,
    87: 24,
    64: 60,
    62: 19,
    54: 34,
    17: 7,
}
LADDERS = {
    1: 38,
    4: 14,
    9: 31,
    21: 42,
    28: 84,
    36: 44,
    51: 67,
    71: 91,
    80: 100,
}

# Bot difficulty presets
BOT_DIFFICULTY = {
    "Chill": {"smart_roll": 0.0, "think_delay": (0.5, 0.9)},
    "Balanced": {"smart_roll": 0.35, "think_delay": (0.7, 1.2)},
    "Spicy": {"smart_roll": 0.7, "think_delay": (0.9, 1.4)},
}

# Utilities
def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, "assets", rel)

def load_sound(name, vol=0.5):
    try:
        s = pygame.mixer.Sound(resource_path(name))
        s.set_volume(vol)
        return s
    except Exception:
        return None

def blit_text(surface, text, pos, font, color=WHITE, max_width=None, line_height=1.3):
    words = text.split(" ")
    x, y = pos
    space = font.size(" ")[0]
    line = []
    for word in words:
        line.append(word)
        w = font.size(" ".join(line))[0]
        if max_width and w > max_width:
            line.pop()
            surface.blit(font.render(" ".join(line), True, color), (x, y))
            y += int(font.get_linesize() * line_height)
            line = [word]
    if line:
        surface.blit(font.render(" ".join(line), True, color), (x, y))

def number_to_coord(n):
    # n from 1..100
    n -= 1
    row = n // BOARD_SIZE
    col = n % BOARD_SIZE
    if row % 2 == 1:
        col = BOARD_SIZE - 1 - col
    x = MARGIN + col * CELL + CELL // 2
    y = HEIGHT - MARGIN - row * CELL - CELL // 2 - 20
    return x, y

def draw_dice(surface, x, y, size, value):
    r = size // 8
    rect = pygame.Rect(x, y, size, size)
    gfxdraw.box(surface, rect, (240,240,240,255))
    pygame.draw.rect(surface, (210,210,210), rect, border_radius=12)
    pygame.draw.rect(surface, (130,130,130), rect, 2, border_radius=12)

    # pip positions
    cx, cy = x + size//2, y + size//2
    off = size//4
    pips = {
        1: [(cx, cy)],
        2: [(cx-off, cy-off), (cx+off, cy+off)],
        3: [(cx-off, cy-off), (cx, cy), (cx+off, cy+off)],
        4: [(cx-off, cy-off), (cx+off, cy-off), (cx-off, cy+off), (cx+off, cy+off)],
        5: [(cx-off, cy-off), (cx+off, cy-off), (cx, cy), (cx-off, cy+off), (cx+off, cy+off)],
        6: [(cx-off, cy-off), (cx+off, cy-off), (cx-off, cy), (cx+off, cy), (cx-off, cy+off), (cx+off, cy+off)]
    }
    for px, py in pips[value]:
        gfxdraw.filled_circle(surface, int(px), int(py), r, (30,30,30))
        gfxdraw.aacircle(surface, int(px), int(py), r, (30,30,30))

def bezier(points, steps=50):
    def lerp(a,b,t): return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)
    def interp(pts,t):
        while len(pts) > 1:
            pts = [lerp(pts[i], pts[i+1], t) for i in range(len(pts)-1)]
        return pts[0]
    return [interp(points, i/steps) for i in range(steps+1)]

def token_pos_with_offset(tile, offset_idx):
    x,y = number_to_coord(tile)
    # offset so tokens don't overlap completely
    angle = offset_idx * (math.pi/2)
    dx = int(10 * math.cos(angle))
    dy = int(10 * math.sin(angle))
    return x+dx, y+dy

class Button:
    def __init__(self, rect, text, font):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.hover = False

    def draw(self, surf):
        color = (50, 56, 72) if not self.hover else (60, 66, 86)
        pygame.draw.rect(surf, color, self.rect, border_radius=12)
        pygame.draw.rect(surf, (120, 130, 160), self.rect, 2, border_radius=12)
        label = self.font.render(self.text, True, (230, 235, 255))
        surf.blit(label, (self.rect.centerx - label.get_width()//2, self.rect.centery - label.get_height()//2))

    def update(self, mouse):
        self.hover = self.rect.collidepoint(mouse)

    def clicked(self, mouse, clicked):
        return self.hover and clicked

class Player:
    def __init__(self, name, color, is_human=False, difficulty="Balanced"):
        self.name = name
        self.color = color
        self.is_human = is_human
        self.tile = 1
        self.won = False
        self.difficulty = difficulty

    def reset(self):
        self.tile = 1
        self.won = False

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.screen = pygame.display.set_mode((WIDTH+SIDEPANEL_W, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("arial", 20)
        self.big = pygame.font.SysFont("arial", 36, bold=True)
        self.huge = pygame.font.SysFont("arial", 72, bold=True)

        # Sounds
        self.s_roll = load_sound("dice.wav", 0.5)
        self.s_ladder = load_sound("ladder.wav", 0.5)
        self.s_snake = load_sound("snake.wav", 0.5)
        self.s_move = load_sound("move.wav", 0.25)
        self.s_win = load_sound("win.wav", 0.7)
        self.music = resource_path("bg_music.wav")
        try:
            pygame.mixer.music.load(self.music)
            pygame.mixer.music.set_volume(0.25)
        except Exception:
            pass

        self.show_numbers = False
        self.fast_mode = False

        # Players
        self.players = [
            Player("You", PLAYER_COLORS[0], is_human=True),
            Player("Bot A", PLAYER_COLORS[1], difficulty="Chill"),
            Player("Bot B", PLAYER_COLORS[2], difficulty="Balanced"),
            Player("Bot C", PLAYER_COLORS[3], difficulty="Spicy"),
        ]
        self.turn = 0
        self.rolling = False
        self.dice_value = 1
        self.animating = False
        self.move_queue = []
        self.message = "Welcome to ITM Snake Game!"

        self.state = "menu"  # menu, playing, gameover
        self.menu_selection = 0

        self.roll_button = Button((WIDTH+30, HEIGHT-120, SIDEPANEL_W-60, 60), "Roll Dice (SPACE)", self.big)
        self.new_game()

    def new_game(self):
        for p in self.players:
            p.reset()
        self.turn = 0
        self.dice_value = 1
        self.rolling = False
        self.animating = False
        self.move_queue = []
        self.message = "Game started! You're Blue."
        self.state = "playing"
        try:
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    def current_player(self):
        return self.players[self.turn]

    # ----------- Drawing ---------------
    def draw_board(self, surf):
        # background
        surf.fill(BG)
        # soft vignette
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (255,255,255,10), (0,0,WIDTH,HEIGHT), border_radius=20)
        surf.blit(overlay, (0,0))

        # board base
        board_rect = pygame.Rect(MARGIN-10, HEIGHT- MARGIN - BOARD_SIZE*CELL -10 -20, BOARD_SIZE*CELL+20, BOARD_SIZE*CELL+20)
        pygame.draw.rect(surf, (35, 40, 55), board_rect, border_radius=16)
        pygame.draw.rect(surf, (80, 90, 120), board_rect, 2, border_radius=16)

        # grid cells with alternating colors
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                x = MARGIN + c*CELL
                y = HEIGHT - MARGIN - (r+1)*CELL - 20
                rect = pygame.Rect(x, y, CELL, CELL)
                col = (60, 75, 105) if (r+c)%2==0 else (55, 70, 98)
                pygame.draw.rect(surf, col, rect)
        # numbers
        if self.show_numbers:
            for n in range(1, 101):
                x, y = number_to_coord(n)
                label = self.font.render(str(n), True, (230,230,230))
                surf.blit(label, (x - label.get_width()//2, y - CELL//2 + 4))

        # draw ladders
        for a,b in LADDERS.items():
            x1,y1 = number_to_coord(a)
            x2,y2 = number_to_coord(b)
            ctrl = ((x1+x2)//2 + random.randint(-20,20), (y1+y2)//2 - 120)
            pts = bezier([(x1,y1),(ctrl),(x2,y2)], 60)
            for i in range(len(pts)-1):
                pygame.draw.line(surf, (180, 220, 180), pts[i], pts[i+1], 8)
            # rungs
            for t in range(8, 54, 8):
                p = pts[t]
                ang = math.atan2(y2-y1, x2-x1) + math.pi/2
                dx, dy = 12*math.cos(ang), 12*math.sin(ang)
                pygame.draw.line(surf, (220, 240, 220), (p[0]-dx,p[1]-dy), (p[0]+dx,p[1]+dy), 3)

        # draw snakes
        for a,b in SNAKES.items():
            x1,y1 = number_to_coord(a)
            x2,y2 = number_to_coord(b)
            ctrl1 = (x1 + (x2-x1)*0.3 + random.randint(-40,40), y1 + (y2-y1)*0.2 + random.randint(-40,40))
            ctrl2 = (x1 + (x2-x1)*0.6 + random.randint(-40,40), y1 + (y2-y1)*0.7 + random.randint(-40,40))
            pts = bezier([(x1,y1), ctrl1, ctrl2, (x2,y2)], 80)
            # body
            for i in range(len(pts)-1):
                w = 14 + 6*math.sin(i*0.3)
                pygame.draw.line(surf, (180, 90, 90), pts[i], pts[i+1], int(max(2,w)))
            # head
            hx, hy = pts[5]
            pygame.draw.circle(surf, (200, 120, 120), (int(hx), int(hy)), 12)
            gfxdraw.aacircle(surf, int(hx), int(hy), 12, (80,30,30))
            # eyes
            pygame.draw.circle(surf, (10,10,10), (int(hx-4), int(hy-2)), 2)
            pygame.draw.circle(surf, (10,10,10), (int(hx+4), int(hy-2)), 2)

    def draw_sidepanel(self, surf):
        x0 = WIDTH
        pygame.draw.rect(surf, (28, 30, 44), (x0, 0, SIDEPANEL_W, HEIGHT))
        pygame.draw.rect(surf, (90, 100, 130), (x0, 0, SIDEPANEL_W, HEIGHT), 2)

        title = self.big.render(TITLE, True, (235, 240, 255))
        surf.blit(title, (x0 + 20, 20))

        # Player list
        y = 80
        for i,p in enumerate(self.players):
            turn_marker = "▶ " if i == self.turn and self.state=="playing" else "   "
            label = self.font.render(f"{turn_marker}{p.name} - Tile {p.tile}", True, p.color)
            surf.blit(label, (x0 + 20, y))
            y += 28

        # Dice
        surf.blit(self.font.render("Dice:", True, LIGHT), (x0+20, y+10))
        draw_dice(surf, x0+90, y, 72, self.dice_value)
        y += 100

        # Buttons
        self.roll_button.draw(surf)
        kb = self.font.render("Controls: SPACE Roll | N New Game | F Fast | G Grid | P Pause Music", True, (210,210,230))
        surf.blit(kb, (x0+20, HEIGHT-170))

        # Message
        pygame.draw.rect(surf, (35, 40, 58), (x0+20, 350, SIDEPANEL_W-40, 160), border_radius=12)
        pygame.draw.rect(surf, (110, 120, 150), (x0+20, 350, SIDEPANEL_W-40, 160), 2, border_radius=12)
        blit_text(surf, self.message, (x0+30, 360), self.font, (230,235,255), SIDEPANEL_W-60)

    def draw_tokens(self, surf):
        for i,p in enumerate(self.players):
            x,y = token_pos_with_offset(p.tile, i)
            pygame.draw.circle(surf, (15,15,15), (x,y+2), 14)
            pygame.draw.circle(surf, p.color, (x,y), 14)
            pygame.draw.circle(surf, (230,230,230), (x,y), 14, 2)

    def render(self):
        self.draw_board(self.screen)
        self.draw_tokens(self.screen)
        self.draw_sidepanel(self.screen)
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "gameover":
            self.draw_gameover()
        pygame.display.flip()

    def draw_menu(self):
        overlay = pygame.Surface((WIDTH+SIDEPANEL_W, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,200))
        self.screen.blit(overlay, (0,0))
        t = self.huge.render("ITM Snake Game", True, (255,255,255))
        self.screen.blit(t, (WIDTH//2 - t.get_width()//2, 120))
        blit_text(self.screen, "1 Human + 3 Bots • Smooth animations • Music & SFX", (WIDTH//2-250, 210), self.big, (230,230,255))

        opts = ["Start Game", "Toggle Numbers", "Quit"]
        for i, o in enumerate(opts):
            col = ACCENT if i == self.menu_selection else WHITE
            label = self.big.render(o, True, col)
            self.screen.blit(label, (WIDTH//2 - label.get_width()//2, 320 + i*60))

    def draw_gameover(self):
        overlay = pygame.Surface((WIDTH+SIDEPANEL_W, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,200))
        self.screen.blit(overlay, (0,0))
        t = self.huge.render("Game Over", True, (255,255,255))
        self.screen.blit(t, (WIDTH//2 - t.get_width()//2, 140))
        w = self.winner
        msg = f"{w.name} wins! Press N for New Game."
        self.screen.blit(self.big.render(msg, True, (240,240,255)), (WIDTH//2 - 260, 260))

    # ----------- Game Logic ---------------
    def smart_bot_roll(self, player, base_roll):
        # Chance to "nudge" the roll toward ladders or away from snakes
        cfg = BOT_DIFFICULTY.get(player.difficulty, BOT_DIFFICULTY["Balanced"])
        if random.random() > cfg["smart_roll"]:
            return base_roll
        best = base_roll
        best_score = -1e9
        for r in range(1,7):
            pos = player.tile + r
            if pos > 100: pos = 100 - (pos-100)  # bounce back
            score = 0
            if pos in LADDERS: score += 50 + (LADDERS[pos]-pos)
            if pos in SNAKES: score -= 60 + (pos-SNAKES[pos])
            score += (pos - player.tile) * 0.1
            if pos == 100: score += 1000
            if score > best_score:
                best_score = score
                best = r
        return best

    def roll_dice(self, player):
        if self.s_roll: self.s_roll.play()
        # animated roll
        for _ in range(12 if not self.fast_mode else 4):
            self.dice_value = random.randint(1,6)
            self.render()
            self.clock.tick(30)
        value = random.randint(1,6)
        if not player.is_human:
            value = self.smart_bot_roll(player, value)
        self.dice_value = value
        return value

    def move_player(self, player, steps):
        target = player.tile + steps
        if target > 100:
            # bounce back
            target = 100 - (target - 100)

        # animate step by step
        while player.tile != target:
            player.tile += 1 if player.tile < target else -1
            if self.s_move and not self.fast_mode: self.s_move.play()
            self.render()
            self.clock.tick(12 if not self.fast_mode else 40)

        # check snakes/ladders
        if player.tile in LADDERS:
            dest = LADDERS[player.tile]
            if self.s_ladder: self.s_ladder.play()
            self.message = f"{player.name} climbs ladder to {dest}!"
            self.animate_jump(player.tile, dest, color=(180,240,180))
            player.tile = dest
        elif player.tile in SNAKES:
            dest = SNAKES[player.tile]
            if self.s_snake: self.s_snake.play()
            self.message = f"Oh no! {player.name} bitten by snake to {dest}."
            self.animate_jump(player.tile, dest, color=(240,170,170))
            player.tile = dest

        if player.tile == 100:
            player.won = True
            if self.s_win: self.s_win.play()
            self.winner = player
            self.state = "gameover"

    def animate_jump(self, a, b, color=(255,255,255)):
        ax, ay = number_to_coord(a)
        bx, by = number_to_coord(b)
        steps = 28 if not self.fast_mode else 12
        for i in range(steps+1):
            t = i/steps
            x = ax + (bx-ax)*t
            y = ay + (by-ay)*t - 80*math.sin(math.pi*t)
            self.draw_board(self.screen)
            self.draw_tokens(self.screen)
            pygame.draw.circle(self.screen, color, (int(x), int(y)), 10)
            self.draw_sidepanel(self.screen)
            pygame.display.flip()
            self.clock.tick(60)

    def next_turn(self):
        self.turn = (self.turn + 1) % len(self.players)

    def update(self, dt):
        pass

    def handle_events(self):
        mouse = pygame.mouse.get_pos()
        clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if self.state == "menu":
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.menu_selection = (self.menu_selection - 1) % 3
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        self.menu_selection = (self.menu_selection + 1) % 3
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.menu_selection == 0: self.state="playing"; self.new_game()
                        elif self.menu_selection == 1: self.show_numbers = not self.show_numbers
                        else: pygame.quit(); sys.exit()
                elif self.state == "playing":
                    if event.key == pygame.K_SPACE:
                        clicked = True
                    if event.key == pygame.K_g:
                        self.show_numbers = not self.show_numbers
                    if event.key == pygame.K_f:
                        self.fast_mode = not self.fast_mode
                    if event.key == pygame.K_n:
                        self.new_game()
                    if event.key == pygame.K_p:
                        if pygame.mixer.music.get_busy():
                            pygame.mixer.music.pause()
                        else:
                            pygame.mixer.music.unpause()
                elif self.state == "gameover":
                    if event.key == pygame.K_n:
                        self.new_game()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = True

        if self.state == "playing":
            self.roll_button.update(mouse)
            if self.current_player().is_human:
                if self.roll_button.clicked(mouse, clicked) or clicked:
                    self.take_turn(self.current_player())
            else:
                # Bot turn with small think delay
                cfg = BOT_DIFFICULTY.get(self.current_player().difficulty, BOT_DIFFICULTY["Balanced"])
                delay = random.uniform(*cfg["think_delay"])
                pygame.time.wait(int(delay*1000))
                self.take_turn(self.current_player())

    def take_turn(self, player):
        if self.state != "playing": return
        if player.won: return
        self.message = f"{player.name} rolling..."
        self.render()
        val = self.roll_dice(player)
        self.message = f"{player.name} rolled a {val}!"
        self.move_player(player, val)
        if self.state == "playing":
            self.next_turn()

    def run(self):
        # start at menu
        self.state = "menu"
        while True:
            dt = self.clock.tick(FPS)/1000.0
            self.handle_events()
            self.update(dt)
            self.render()

if __name__ == "__main__":
    Game().run()

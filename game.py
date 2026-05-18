import pygame
import sys
import random

# Global constants and game configuration
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 750
BOARD_TOP_OFFSET = 150

BG_BASE = 15, 18, 25
BOARD_BG = 22, 26, 35
ACCENT_CYAN = 0, 240, 255
ACCENT_ORANGE = 255, 170, 0
CHEST_COLOR = 255, 215, 0
TEXT_WHITE = 240, 240, 245
TEXT_MUTED = 120, 130, 150
GRID_LINE = 45, 55, 75
BLACK_PIECE = 20, 20, 20
WHITE_PIECE = 230, 230, 230

# Update menu state
MENU_MODE = 0
MENU_CONFIGURE = 1 
MENU_DIFFICULTY = 3
PLAYING = 4
GAME_OVER = 5
VIEWING_RESULT_BOARD = 6 

MODE_PVP = 1
MODE_PVAI = 2

DIFF_EASY = 1
DIFF_MEDIUM = 2
DIFF_HARD = 3

FONT_TITLE_SIZE = 44
FONT_LARGE_SIZE = 32
FONT_SMALL_SIZE = 22
FONT_MONO_SIZE = 18

AI_DEPTH_MEDIUM = 2
AI_DEPTH_HARD = 4

class AIEngine:
    """
    1. Class managing the AI controlling the computer opponent.
       Includes Minimax, Alpha-Beta Pruning, and Greedy algorithms to decide moves.
    """
    def __init__(self, difficulty=DIFF_MEDIUM):
        """
        1. Initialize the AI system with default difficulty, set up the tree search depth table 
           and the random error rate table corresponding to each difficulty level.
        2. Args:
           - difficulty (int): Constant specifying the initial difficulty level.
        3. Returns: None
        """
        self.difficulty = difficulty
        self.depth_map = {
            DIFF_MEDIUM: AI_DEPTH_MEDIUM,
            DIFF_HARD: AI_DEPTH_HARD
        }
        self.error_rate_map = {
            DIFF_EASY: 0.40,
            DIFF_MEDIUM: 0.20,
            DIFF_HARD: 0.0
        }
        self.nodes_searched = 0
    
    def set_difficulty(self, difficulty):
        """
        1. Update the AI difficulty when the player reselects it in the menu.
        2. Args:
           - difficulty (int): Constant specifying the new difficulty level.
        3. Returns: None
        """
        self.difficulty = difficulty

    def _get_flips(self, board, r, c, color, size):
        """
        1. Simulate the flipping rules on a virtual board matrix, supporting the prediction of 
           potential moves without changing the actual game state.
        2. Args:
           - board (list): 2D array representing the current board.
           - r (int): Row index.
           - c (int): Column index.
           - color (tuple): Color of the piece being considered.
           - size (int): Size of the board.
        3. Returns: list - List of coordinates of the flipped pieces.
        """
        if board[r][c] is not None:
            return []
        flips = []
        opp = WHITE_PIECE if color == BLACK_PIECE else BLACK_PIECE
        dirs = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        for dr, dc in dirs:
            path = []
            nr, nc = r + dr, c + dc
            while 0 <= nr < size and 0 <= nc < size and board[nr][nc] == opp:
                path.append((nr, nc))
                nr += dr
                nc += dc
            if path and 0 <= nr < size and 0 <= nc < size and board[nr][nc] == color:
                flips.extend(path)
        return flips

    def _get_valid_moves(self, board, color, size):
        """
        1. Find and compile all valid moves for a side on the simulated board.
        2. Args:
           - board (list): 2D array representing the board.
           - color (tuple): Color of the piece being considered.
           - size (int): Size of the board.
        3. Returns: dict - Dictionary containing move coordinates and corresponding lists of flipped pieces.
        """
        moves = {}
        for r in range(size):
            for c in range(size):
                f = self._get_flips(board, r, c, color, size)
                if f:
                    moves[(r, c)] = f
        return moves

    def _evaluate(self, board, color, size):
        """
        1. Heuristic scoring for the current board state, calculated based on piece count, 
           strategic corner control, and mobility.
        2. Args:
           - board (list): 2D array representing the board.
           - color (tuple): Color of the AI pieces.
           - size (int): Size of the board.
        3. Returns: int - Evaluation score of the state.
        """
        my = sum(row.count(color) for row in board)
        opp = sum(row.count(WHITE_PIECE if color == BLACK_PIECE else BLACK_PIECE) for row in board)
        corners = [(0,0), (0,size-1), (size-1,0), (size-1,size-1)]
        cb = 0
        for r, c in corners:
            if board[r][c] == color:
                cb += 10
            elif board[r][c] is not None:
                cb -= 10
        mob = len(self._get_valid_moves(board, color, size))
        return (my - opp) * 2 + cb + mob

    def _simulate_move(self, board, chests, move, color, size):
        """
        1. Simulate a move on the board, update the chest count, and check if the player gets an extra turn.
        2. Args:
           - board (list): 2D array representing the board.
           - chests (list): List of current chest coordinates.
           - move (tuple): Coordinates of the move to simulate.
           - color (tuple): Color of the piece making the move.
           - size (int): Size of the board.
        3. Returns: tuple - New board, new chest list, and extra turn flag.
        """
        new_b = [row[:] for row in board]
        new_c = chests[:]
        r, c = move
        flips = self._get_flips(new_b, r, c, color, size)
        new_b[r][c] = color
        for fr, fc in flips:
            new_b[fr][fc] = color
        
        extra_turn = False
        if move in new_c:
            new_c.remove(move)
            pcs = [(rr, cc) for rr in range(size) for cc in range(size) if new_b[rr][cc] == color]
            if pcs:
                rr, cc = pcs[0]
                new_b[rr][cc] = None
            extra_turn = True
            
        return new_b, new_c, extra_turn
    
    def get_best_move(self, app, bypass_error=False):
        """
        1. Find the best move for the AI based on the selected difficulty, which may include 
           random errors depending on the error rate.
        2. Args:
           - app (EndfieldOthello): Main game object containing the global state.
           - bypass_error (bool): Ignore the random error mechanic if set to True.
        3. Returns: tuple - Coordinates of the best move, or None if unavailable.
        """
        self.nodes_searched = 0
        valid_moves = self._get_valid_moves(app.board, app.current_turn, app.board_size)
        
        if not valid_moves:
            return None

        if not bypass_error:
            error_rate = self.error_rate_map.get(self.difficulty, 0.0)
            if random.random() < error_rate:
                return random.choice(list(valid_moves.keys()))

        depth = self.depth_map.get(self.difficulty, AI_DEPTH_MEDIUM)
        
        if self.difficulty == DIFF_EASY:
            return self._greedy_move(app.board, app.current_turn, app.chests, app.board_size)
        
        best_score = float('-inf')
        best_move = None
        
        for move in valid_moves:
            nb, nc, extra = self._simulate_move(app.board, app.chests, move, app.current_turn, app.board_size)
            next_turn = app.current_turn if extra else (WHITE_PIECE if app.current_turn == BLACK_PIECE else BLACK_PIECE)
            next_max = extra 
            
            if self.difficulty == DIFF_HARD:
                score = self._alpha_beta(nb, nc, next_turn, depth - 1, float('-inf'), float('inf'), next_max, app.current_turn, app.board_size)
            else:
                score = self._minimax(nb, nc, next_turn, depth - 1, next_max, app.current_turn, app.board_size)
                
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def _greedy_move(self, board, turn, chests, size):
        """
        1. Greedy search algorithm for easy difficulty, prioritizing capturing the most pieces and chests.
        2. Args:
           - board (list): 2D array representing the board.
           - turn (tuple): Color of the considered piece.
           - chests (list): List of chest coordinates.
           - size (int): Size of the board.
        3. Returns: tuple - Coordinates of the best greedy move.
        """
        valid = self._get_valid_moves(board, turn, size)
        best_m = None
        max_f = -1
        for m, f in valid.items():
            cnt = len(f)
            if m in chests: cnt += 3
            if cnt > max_f:
                max_f = cnt
                best_m = m
        return best_m
    
    def _minimax(self, board, chests, turn, depth, is_max, ai_color, size):
        """
        1. Standard tree search algorithm used for medium and hard difficulty to find the optimal scoring move.
        2. Args:
           - board (list): 2D array representing the board.
           - chests (list): List of chest coordinates.
           - turn (tuple): Color of the moving piece.
           - depth (int): Remaining depth of the search tree.
           - is_max (bool): Flag indicating if this is a maximizing step.
           - ai_color (tuple): Original color of the AI piece.
           - size (int): Size of the board.
        3. Returns: float - Evaluation score of the current branch.
        """
        self.nodes_searched += 1
        
        valid = self._get_valid_moves(board, turn, size)
        if depth == 0 or not valid:
            opp = WHITE_PIECE if turn == BLACK_PIECE else BLACK_PIECE
            if not valid and not self._get_valid_moves(board, opp, size):
                return self._evaluate(board, ai_color, size)
            
            if not valid:
                return self._minimax(board, chests, opp, depth, not is_max, ai_color, size)
                
            return self._evaluate(board, ai_color, size)

        if is_max:
            max_eval = float('-inf')
            for move in valid:
                nb, nc, extra = self._simulate_move(board, chests, move, turn, size)
                next_turn = turn if extra else (WHITE_PIECE if turn == BLACK_PIECE else BLACK_PIECE)
                next_max = True if extra else False
                ev = self._minimax(nb, nc, next_turn, depth - 1, next_max, ai_color, size)
                max_eval = max(max_eval, ev)
            return max_eval
        else:
            min_eval = float('inf')
            for move in valid:
                nb, nc, extra = self._simulate_move(board, chests, move, turn, size)
                next_turn = turn if extra else (WHITE_PIECE if turn == BLACK_PIECE else BLACK_PIECE)
                next_max = False if extra else True
                ev = self._minimax(nb, nc, next_turn, depth - 1, next_max, ai_color, size)
                min_eval = min(min_eval, ev)
            return min_eval
            
    def _alpha_beta(self, board, chests, turn, depth, alpha, beta, is_max, ai_color, size):
        """
        1. Pruning optimization combined with tree search used for hard difficulty, 
           helping the AI evaluate deeper with higher efficiency.
        2. Args:
           - board (list): 2D array representing the board.
           - chests (list): List of chest coordinates.
           - turn (tuple): Color of the moving piece.
           - depth (int): Remaining depth of the search tree.
           - alpha (float): Alpha value for pruning.
           - beta (float): Beta value for pruning.
           - is_max (bool): Flag indicating if this is a maximizing step.
           - ai_color (tuple): Original color of the AI piece.
           - size (int): Size of the board.
        3. Returns: float - Optimal score calculated after pruning.
        """
        self.nodes_searched += 1
        
        valid = self._get_valid_moves(board, turn, size)
        if depth == 0 or not valid:
            opp = WHITE_PIECE if turn == BLACK_PIECE else BLACK_PIECE
            if not valid and not self._get_valid_moves(board, opp, size):
                return self._evaluate(board, ai_color, size)
            
            if not valid:
                return self._alpha_beta(board, chests, opp, depth, alpha, beta, not is_max, ai_color, size)
                
            return self._evaluate(board, ai_color, size)

        if is_max:
            max_eval = float('-inf')
            for move in valid:
                nb, nc, extra = self._simulate_move(board, chests, move, turn, size)
                next_turn = turn if extra else (WHITE_PIECE if turn == BLACK_PIECE else BLACK_PIECE)
                next_max = True if extra else False
                ev = self._alpha_beta(nb, nc, next_turn, depth - 1, alpha, beta, next_max, ai_color, size)
                max_eval = max(max_eval, ev)
                alpha = max(alpha, ev)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in valid:
                nb, nc, extra = self._simulate_move(board, chests, move, turn, size)
                next_turn = turn if extra else (WHITE_PIECE if turn == BLACK_PIECE else BLACK_PIECE)
                next_max = False if extra else True
                ev = self._alpha_beta(nb, nc, next_turn, depth - 1, alpha, beta, next_max, ai_color, size)
                min_eval = min(min_eval, ev)
                beta = min(beta, ev)
                if beta <= alpha:
                    break
            return min_eval
    
    def reset_cache(self):
        """
        1. Reset the counter tracking the number of node points traversed by the AI in a turn.
        2. Args: None
        3. Returns: None
        """
        self.nodes_searched = 0

class EndfieldOthello:
    """
    Class managing the game rules logic and the graphical interface of the game.
    """
    def __init__(self):
        """
        1. Initialize the graphics and audio library, set up the application window, fonts, 
           and default states of the game.
        2. Args: None
        3. Returns: None
        """
        pygame.init()
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Endfield Protocol")
        
        self.fonts = {}
        try:
            self.fonts['title'] = pygame.font.SysFont("consolas", FONT_TITLE_SIZE, bold=True)
            self.fonts['large'] = pygame.font.SysFont("consolas", FONT_LARGE_SIZE)
            self.fonts['small'] = pygame.font.SysFont("consolas", FONT_SMALL_SIZE)
            self.fonts['mono'] = pygame.font.SysFont("consolas", FONT_MONO_SIZE)
        except Exception:
            for k in ['title', 'large', 'small', 'mono']:
                self.fonts[k] = pygame.font.Font(None, FONT_TITLE_SIZE)
            
        try:
            self.sfx_invalid = pygame.mixer.Sound("InvalidMove.mp3")
        except:
            self.sfx_invalid = None

        self.state = MENU_MODE
        self.temp_mode = MODE_PVP
        self.temp_size = 8
        self.temp_color = BLACK_PIECE
        self.temp_difficulty = DIFF_MEDIUM
        self.temp_chests = 8
        
        self.board_size = self.temp_size
        self.cell_size = WINDOW_WIDTH // self.board_size
        self.alert_msg = ""
        self.alert_timer = 0
        self.ai_skipped_timer = 0
        
        self.buttons = {}
        self.ai_engine = None
        self.ai_thinking = False
        self.ai_think_start = 0
        self.ai_delay = 1500

    def init_board(self):
        """
        1. Set up a new board based on the selected configuration, including placing the four 
           initial pieces in the center and randomly distributing chests.
        2. Args: None
        3. Returns: None
        """
        self.board_size = self.temp_size
        self.cell_size = WINDOW_WIDTH // self.board_size
        self.board = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]
        mid = self.board_size // 2
        self.board[mid - 1][mid - 1] = WHITE_PIECE
        self.board[mid][mid] = WHITE_PIECE
        self.board[mid - 1][mid] = BLACK_PIECE
        self.board[mid][mid - 1] = BLACK_PIECE
        self.current_turn = BLACK_PIECE
        self.extra_turn_active = False
        self.loss_pending = 0
        self.alert_timer = 0
        self.ai_skipped_timer = 0
        self.chests = []
        
        self.hint_move = None
        self.hint_count = 3
        
        first_turn_moves = self.get_valid_moves(BLACK_PIECE).keys()
        
        empty_cells = [(r, c) for r in range(self.board_size) for c in range(self.board_size) 
                       if self.board[r][c] is None and (r, c) not in first_turn_moves]
                       
        count = getattr(self, 'temp_chests', 4)
        self.chests = random.sample(empty_cells, min(count, len(empty_cells)))
        
        if self.temp_mode == MODE_PVAI:
            self.ai_engine = AIEngine(self.temp_difficulty)
            if self.temp_color == WHITE_PIECE:
                self.schedule_ai_turn()
        else:
            self.ai_engine = None

    def get_flips(self, r, c, color):
        """
        1. Check if the placed piece position is valid by iterating through the surrounding directions 
           to find opponent pieces that can be flipped on the actual board.
        2. Args:
           - r (int): Row index for the move.
           - c (int): Column index for the move.
           - color (tuple): Color of the side making the move.
        3. Returns: list - List of coordinates of the pieces that will be flipped.
        """
        if self.board[r][c] is not None:
            return []
        flips = []
        opponent = WHITE_PIECE if color == BLACK_PIECE else BLACK_PIECE
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            path = []
            while 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.board[nr][nc] == opponent:
                path.append((nr, nc))
                nr += dr; nc += dc
            if path and 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.board[nr][nc] == color:
                flips.extend(path)
        return flips

    def get_valid_moves(self, color):
        """
        1. Scan the entire board to compile all valid move positions for the current side.
        2. Args:
           - color (tuple): Color of the side to check.
        3. Returns: dict - Dictionary containing valid positions as Keys and the list of flipped pieces as Values.
        """
        moves = {}
        for r in range(self.board_size):
            for c in range(self.board_size):
                flips = self.get_flips(r, c, color)
                if flips: 
                    moves[(r, c)] = flips
        return moves

    def remove_random_piece(self, color):
        """
        1. Find all pieces of a side, then use random.choice to randomly select and remove one piece (reassign to None).
        2. Args:
           - color (tuple): Color of the side that will lose a piece.
        3. Returns: None
        """
        pieces = [(r, c) for r in range(self.board_size) for c in range(self.board_size) if self.board[r][c] == color]
        if pieces: 
            r, c = random.choice(pieces)
            self.board[r][c] = None

    def trigger_chest_effect(self):
        """
        1. Trigger the chest consumption effect, gaining an extra turn in exchange for any one piece.
        2. Args: None
        3. Returns: None
        """
        self.alert_msg = "POWER UP: DOUBLE TURN AND LOSE PIECES"
        self.alert_timer = 150 
        self.remove_random_piece(self.current_turn)
        self.extra_turn_active = True
        self.loss_pending = 1 

    def next_turn(self):
        """
        1. Switch turns between the two sides, skipping the turn if that side has no valid moves, 
           or immediately ending the game if neither side has valid moves.
        2. Args: None
        3. Returns: None
        """
        self.current_turn = WHITE_PIECE if self.current_turn == BLACK_PIECE else BLACK_PIECE
            
        if not self.get_valid_moves(self.current_turn):
            skipped_turn = self.current_turn
            self.current_turn = WHITE_PIECE if self.current_turn == BLACK_PIECE else BLACK_PIECE
                
            if self.temp_mode == MODE_PVAI and skipped_turn != self.temp_color:
                self.ai_skipped_timer = 120
                
            if not self.get_valid_moves(self.current_turn): 
                self.state = GAME_OVER

    def draw_tech_button(self, text, rect_tup, default_col, hover_col, enabled=True):
        """
        1. Draw a Sci-fi style interface button, color change effect on hover, and decorative border.
        2. Args:
           - text (str): Label displayed on the button.
           - rect_tup (tuple): Coordinates and dimensions of the button.
           - default_col (tuple): Default color.
           - hover_col (tuple): Color when hovering over the button.
           - enabled (bool): Status indicating if interaction is allowed.
        3. Returns: Rect - Rectangle frame of the button used to catch mouse events.
        """
        rect = pygame.Rect(rect_tup)
        is_hovered = enabled and rect.collidepoint(pygame.mouse.get_pos())
        current_color = hover_col if is_hovered else (default_col if enabled else (60, 60, 70))
        
        if is_hovered:
            s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            s.fill((*current_color[:3], 40))
            self.screen.blit(s, rect)
        
        pygame.draw.rect(self.screen, current_color, rect, 2)
        length = 12
        corners = [(rect.x, rect.y, rect.x+length, rect.y),
                   (rect.x, rect.y, rect.x, rect.y+length),
                   (rect.right, rect.bottom, rect.right-length, rect.bottom),
                   (rect.right, rect.bottom, rect.right, rect.bottom-length)]
        for x1, y1, x2, y2 in corners:
            pygame.draw.line(self.screen, current_color, (x1, y1), (x2, y2), 4)
        
        txt = self.fonts['small'].render(f"[{text}]", True, current_color if is_hovered else TEXT_WHITE)
        self.screen.blit(txt, txt.get_rect(center=rect.center))
        return rect

    def draw_grid_background(self):
        """
        1. Draw the background interface as faint grid lines to decorate the Menu screen.
        2. Args: None
        3. Returns: None
        """
        self.screen.fill(BG_BASE)
        for y in range(0, WINDOW_HEIGHT, 40):
            pygame.draw.line(self.screen, (20, 24, 32), (0, y), (WINDOW_WIDTH, y), 1)

    def draw_menu_mode(self):
        """
        1. Display the main screen to choose between two-player mode or playing against the computer.
        2. Args: None
        3. Returns: None
        """
        self.draw_grid_background()
        self.screen.blit(self.fonts['mono'].render("SYS.INIT // COMBAT_MODE_SELECTION", True, ACCENT_CYAN), (20, 20))
        title = self.fonts['title'].render("SELECT GAME MODE", True, TEXT_WHITE)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 180))
        btn_pvp = self.draw_tech_button(" TWO PLAYERS ", (150, 280, 300, 60), TEXT_MUTED, ACCENT_CYAN)
        btn_pvai = self.draw_tech_button(" VS ARTIFICIAL INTELLIGENCE ", (100, 360, 400, 60), TEXT_MUTED, ACCENT_CYAN)
        desc = self.fonts['small'].render("Choose your battle configuration", True, TEXT_MUTED)
        self.screen.blit(desc, (WINDOW_WIDTH//2 - desc.get_width()//2, 450))
        self.buttons = {'pvp': btn_pvp, 'pvai': btn_pvai}

    def draw_menu_configure(self):
        """
        1. Display the detailed configuration screen, allowing selection of board size, player color, 
           and the number of chests on the board.
        2. Args: None
        3. Returns: None
        """
        self.draw_grid_background()
        self.screen.blit(self.fonts['mono'].render("SYS.INIT // COMBAT_CONFIGURATION", True, ACCENT_CYAN), (20, 20))
        
        title = self.fonts['title'].render("CONFIGURE GAME", True, TEXT_WHITE)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 120))
        
        lbl_size = self.fonts['small'].render("GRID SIZE", True, TEXT_MUTED)
        self.screen.blit(lbl_size, (WINDOW_WIDTH//2 - lbl_size.get_width()//2, 220))
        
        btn_w = 120
        spacing = 20
        total_w = btn_w * 3 + spacing * 2
        start_x = (WINDOW_WIDTH - total_w) // 2
        
        btn_6x6 = self.draw_tech_button(" 6 x 6 ", (start_x, 260, btn_w, 45), ACCENT_CYAN if self.temp_size == 6 else TEXT_MUTED, ACCENT_CYAN)
        btn_8x8 = self.draw_tech_button(" 8 x 8 ", (start_x + btn_w + spacing, 260, btn_w, 45), ACCENT_CYAN if self.temp_size == 8 else TEXT_MUTED, ACCENT_CYAN)
        btn_10x10 = self.draw_tech_button("10 x 10", (start_x + (btn_w + spacing) * 2, 260, btn_w, 45), ACCENT_CYAN if self.temp_size == 10 else TEXT_MUTED, ACCENT_CYAN)
        
        lbl_alliance = self.fonts['small'].render("ALLIANCE", True, TEXT_MUTED)
        self.screen.blit(lbl_alliance, (WINDOW_WIDTH//2 - lbl_alliance.get_width()//2, 340))
        
        btn_w_ali = 180
        total_w_ali = btn_w_ali * 2 + spacing
        start_x_ali = (WINDOW_WIDTH - total_w_ali) // 2
        
        btn_black = self.draw_tech_button(" BLACK FIRST ", (start_x_ali, 380, btn_w_ali, 45), ACCENT_CYAN if self.temp_color == BLACK_PIECE else TEXT_MUTED, ACCENT_CYAN)
        btn_white = self.draw_tech_button(" WHITE ", (start_x_ali + btn_w_ali + spacing, 380, btn_w_ali, 45), ACCENT_CYAN if self.temp_color == WHITE_PIECE else TEXT_MUTED, ACCENT_CYAN)
        
        lbl_chest = self.fonts['small'].render("CHEST COUNT", True, TEXT_MUTED)
        self.screen.blit(lbl_chest, (WINDOW_WIDTH//2 - lbl_chest.get_width()//2, 460))
        
        chest_options = [4, 6, 8]
        
        if not hasattr(self, 'temp_chests') or self.temp_chests not in chest_options:
            self.temp_chests = chest_options[0]
            
        self.buttons = {'6x6': btn_6x6, '8x8': btn_8x8, '10x10': btn_10x10, 'black': btn_black, 'white': btn_white}
        
        btn_w_chest = 75
        num_chests = len(chest_options)
        total_w_chest = num_chests * btn_w_chest + (num_chests - 1) * spacing
        start_x_chest = (WINDOW_WIDTH - total_w_chest) // 2
        
        for opt in chest_options:
            btn = self.draw_tech_button(f" {opt} ", (start_x_chest, 500, btn_w_chest, 45), ACCENT_CYAN if self.temp_chests == opt else TEXT_MUTED, ACCENT_CYAN)
            self.buttons[f'chest_{opt}'] = btn
            start_x_chest += btn_w_chest + spacing
            
        btn_proceed = self.draw_tech_button(" PROCEED ", (WINDOW_WIDTH//2 - 100, 600, 200, 55), TEXT_MUTED, ACCENT_CYAN)
        self.buttons['proceed'] = btn_proceed

    def draw_menu_difficulty(self):
        """
        1. Display the computer difficulty adjustment screen if the player chooses the versus computer mode.
        2. Args: None
        3. Returns: None
        """
        self.draw_grid_background()
        self.screen.blit(self.fonts['mono'].render("SYS.INIT // AI_DIFFICULTY_CALIBRATION", True, ACCENT_CYAN), (20, 20))
        title = self.fonts['title'].render("SELECT DIFFICULTY", True, TEXT_WHITE)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 180))
        
        btn_easy = self.draw_tech_button(" EASY ", (150, 280, 300, 55), TEXT_MUTED, (100, 255, 100))
        btn_medium = self.draw_tech_button(" MEDIUM ", (150, 350, 300, 55), TEXT_MUTED, ACCENT_CYAN)
        btn_hard = self.draw_tech_button(" HARD ", (150, 420, 300, 55), TEXT_MUTED, ACCENT_ORANGE)
        
        self.buttons = {'easy': btn_easy, 'medium': btn_medium, 'hard': btn_hard}

    def draw_board(self):
        """
        1. Draw the interface of the actual match including the board, pieces, chests, 
           score, valid moves, and notifications.
        2. Args: None
        3. Returns: None
        """
        self.screen.fill(BG_BASE)
        pygame.draw.rect(self.screen, BOARD_BG, (0, 0, WINDOW_WIDTH, BOARD_TOP_OFFSET))
        pygame.draw.line(self.screen, ACCENT_CYAN, (0, BOARD_TOP_OFFSET), (WINDOW_WIDTH, BOARD_TOP_OFFSET), 2)
        
        black_count = sum(row.count(BLACK_PIECE) for row in self.board)
        white_count = sum(row.count(WHITE_PIECE) for row in self.board)
        
        if self.state == VIEWING_RESULT_BOARD:
            turn_txt = "POST-MATCH ANALYSIS"
            turn_color = TEXT_WHITE
            top_btn_txt = "VIEW RESULT"
            top_btn_color = ACCENT_CYAN
            top_btn_action = 'view_result'
            btn_w = 175 
        else:
            is_black_turn = self.current_turn == BLACK_PIECE
            turn_txt = "COMBAT PHASE BLACK" if is_black_turn else "COMBAT PHASE WHITE"
            turn_color = ACCENT_CYAN if is_black_turn else ACCENT_ORANGE
            if self.extra_turn_active:
                turn_txt += " DOUBLE"
                turn_color = CHEST_COLOR
            top_btn_txt = "REBOOT"
            top_btn_color = (255, 80, 80)
            top_btn_action = 'reboot'
            btn_w = 120 
        
        self.screen.blit(self.fonts['mono'].render("ENDFIELD_OS // V1.0.8", True, TEXT_MUTED), (20, 15))
        self.screen.blit(self.fonts['large'].render(turn_txt, True, turn_color), (20, 50))
        self.screen.blit(self.fonts['small'].render(f"BLACK {black_count:02d}  WHITE {white_count:02d}", True, TEXT_WHITE), (20, 95))
        
        alert_y = 125
        if self.alert_timer > 0 and self.state != VIEWING_RESULT_BOARD:
            alert = self.fonts['small'].render(self.alert_msg, True, CHEST_COLOR)
            self.screen.blit(alert, (WINDOW_WIDTH//2 - alert.get_width()//2, alert_y))
            alert_y = 145
        
        if self.ai_thinking and self.state != VIEWING_RESULT_BOARD:
            think_txt = self.fonts['small'].render("AI is thinking...", True, (150, 160, 170))
            think_y = 95 if self.alert_timer > 0 else 120
            self.screen.blit(think_txt, (WINDOW_WIDTH - think_txt.get_width() - 20, think_y))
        elif self.ai_skipped_timer > 0 and self.state != VIEWING_RESULT_BOARD:
            skip_txt = self.fonts['small'].render("AI HAS NO VALID MOVES", True, (255, 100, 100))
            think_y = 95 if self.alert_timer > 0 else 120
            self.screen.blit(skip_txt, (WINDOW_WIDTH - skip_txt.get_width() - 20, think_y))
        
        x_pos = WINDOW_WIDTH - btn_w - 20
        top_right_btn = self.draw_tech_button(top_btn_txt, (x_pos, 15, btn_w, 35), (80, 90, 100), top_btn_color)
        
        self.buttons = {top_btn_action: top_right_btn}
        
        if self.state == PLAYING and self.temp_mode == MODE_PVAI and self.current_turn == self.temp_color and not self.ai_thinking:
            hint_txt = f"HINT: {self.hint_count}"
            hint_w = 110
            hint_x = x_pos - hint_w - 15
            hint_color = (100, 255, 100) if self.hint_count > 0 else TEXT_MUTED
            hint_btn = self.draw_tech_button(hint_txt, (hint_x, 15, hint_w, 35), (80, 90, 100), hint_color, enabled=(self.hint_count > 0))
            self.buttons['hint'] = hint_btn

        pygame.draw.rect(self.screen, BOARD_BG, (0, BOARD_TOP_OFFSET, WINDOW_WIDTH, WINDOW_HEIGHT-BOARD_TOP_OFFSET))
        for x in range(0, WINDOW_WIDTH+1, self.cell_size):
            pygame.draw.line(self.screen, GRID_LINE, (x, BOARD_TOP_OFFSET), (x, WINDOW_HEIGHT))
        for y in range(BOARD_TOP_OFFSET, WINDOW_HEIGHT+1, self.cell_size):
            pygame.draw.line(self.screen, GRID_LINE, (0, y), (WINDOW_WIDTH, y))
        
        for r in range(self.board_size):
            for c in range(self.board_size):
                cx = c * self.cell_size + self.cell_size // 2
                cy = BOARD_TOP_OFFSET + r * self.cell_size + self.cell_size // 2
                
                if (r, c) in self.chests:
                    pygame.draw.rect(self.screen, CHEST_COLOR, (cx-15, cy-10, 30, 20), border_radius=4)
                    pygame.draw.line(self.screen, (0,0,0), (cx-15, cy), (cx+15, cy), 2)
                    pygame.draw.circle(self.screen, (255,255,255), (cx, cy), 3)
                
                if self.board[r][c] is not None:
                    radius = self.cell_size // 2 - 8
                    pygame.draw.circle(self.screen, (0,0,0), (cx, cy+2), radius)
                    pygame.draw.circle(self.screen, self.board[r][c], (cx, cy), radius)
                    inner = (60,60,60) if self.board[r][c] == BLACK_PIECE else (200,200,200)
                    pygame.draw.circle(self.screen, inner, (cx, cy), radius-4, 1)
        
        if self.state == PLAYING:
            valid_moves = self.get_valid_moves(self.current_turn)
            for (r, c) in valid_moves:
                cx = c * self.cell_size + self.cell_size // 2
                cy = BOARD_TOP_OFFSET + r * self.cell_size + self.cell_size // 2
                size = self.cell_size // 8
                
                if (r, c) in self.chests:
                    offset, length = 22, 8
                    corners = [(-1,-1), (1,-1), (-1,1), (1,1)]
                    for sx, sy in corners:
                        x, y = cx + sx*offset, cy + sy*offset
                        pygame.draw.line(self.screen, turn_color, (x, y), (x + sx*length, y), 2)
                        pygame.draw.line(self.screen, turn_color, (x, y), (x, y + sy*length), 2)
                else:
                    pygame.draw.line(self.screen, turn_color, (cx-size, cy), (cx+size, cy), 2)
                    pygame.draw.line(self.screen, turn_color, (cx, cy-size), (cx, cy+size), 2)
                    pygame.draw.circle(self.screen, turn_color, (cx, cy), size+2, 1)
            
            if self.hint_move:
                hr, hc = self.hint_move
                hx = hc * self.cell_size + self.cell_size // 2
                hy = BOARD_TOP_OFFSET + hr * self.cell_size + self.cell_size // 2
                pygame.draw.circle(self.screen, (100, 255, 100), (hx, hy), self.cell_size // 3, 3)

    def draw_game_over(self):
        """
        1. Display the match summary screen, showing the win/loss result along with the final score, 
           and providing buttons to replay, quit, or review the board.
        2. Args: None
        3. Returns: None
        """
        self.draw_grid_background()
        black = sum(row.count(BLACK_PIECE) for row in self.board)
        white = sum(row.count(WHITE_PIECE) for row in self.board)
        if black > white:
            res_txt, res_col = "RESULT BLACK WINS", ACCENT_CYAN
        elif white > black:
            res_txt, res_col = "RESULT WHITE WINS", ACCENT_ORANGE
        else:
            res_txt, res_col = "RESULT STALEMATE", TEXT_WHITE
            
        self.screen.blit(self.fonts['mono'].render("SYS.HALT // SIMULATION_COMPLETE", True, res_col), (20, 20))
        title = self.fonts['title'].render(res_txt, True, res_col)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 220))
        score = self.fonts['large'].render(f"BLACK {black}  WHITE {white}", True, TEXT_WHITE)
        self.screen.blit(score, (WINDOW_WIDTH//2 - score.get_width()//2, 290))
        
        btn_replay = self.draw_tech_button(" REBOOT ", (100, 390, 180, 55), TEXT_MUTED, ACCENT_CYAN)
        btn_quit = self.draw_tech_button(" TERMINATE ", (320, 390, 180, 55), TEXT_MUTED, (255,50,50))
        btn_view_board = self.draw_tech_button(" VIEW BOARD ", (100, 460, 400, 55), TEXT_MUTED, ACCENT_CYAN)
        
        self.buttons = {'replay': btn_replay, 'quit': btn_quit, 'view_board': btn_view_board}

    def schedule_ai_turn(self):
        """
        1. Create a delay between AI decisions, simulating a real person.
        2. Args: None
        3. Returns: None
        """
        if self.temp_mode != MODE_PVAI or self.current_turn == self.temp_color:
            return
        self.ai_thinking = True
        self.ai_think_start = pygame.time.get_ticks()

    def execute_ai_turn(self):
        """
        1. Request the AI engine to calculate a move, then update the board logic and handle 
           additional effects like eating chests or extra turns.
        2. Args: None
        3. Returns: None
        """
        if not self.ai_engine:
            self.ai_thinking = False
            return
            
        best_move = self.ai_engine.get_best_move(self)
        if not best_move:
            self.next_turn()
            self.ai_thinking = False
            return
            
        r, c = best_move
        valid = self.get_valid_moves(self.current_turn)
        
        self.board[r][c] = self.current_turn
        for fr, fc in valid[(r, c)]:
            self.board[fr][fc] = self.current_turn
            
        chest = False
        if (r, c) in self.chests:
            self.chests.remove((r, c))
            self.trigger_chest_effect()
            self.ai_engine.reset_cache()
            chest = True
            
        if self.loss_pending > 0 and not chest:
            self.remove_random_piece(self.current_turn)
            self.loss_pending -= 1
            
        if self.extra_turn_active:
            self.extra_turn_active = False
            if not self.get_valid_moves(self.current_turn):
                self.next_turn()
        else:
            self.next_turn()
            
        self.ai_thinking = False
        if self.temp_mode == MODE_PVAI and self.current_turn != self.temp_color and self.state == PLAYING:
            self.schedule_ai_turn()

    def run(self):
        """
        1. The continuous game loop that handles input events, maintains the game at 60 FPS, 
           and redraws the interfaces per frame.
        2. Args: None
        3. Returns: None
        """
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == MENU_MODE:
                        if 'pvp' in self.buttons and self.buttons['pvp'].collidepoint(event.pos): 
                            self.temp_mode = MODE_PVP; self.state = MENU_CONFIGURE
                        elif 'pvai' in self.buttons and self.buttons['pvai'].collidepoint(event.pos): 
                            self.temp_mode = MODE_PVAI; self.state = MENU_CONFIGURE
                    
                    elif self.state == MENU_CONFIGURE:
                        if '6x6' in self.buttons and self.buttons['6x6'].collidepoint(event.pos): 
                            self.temp_size = 6
                        elif '8x8' in self.buttons and self.buttons['8x8'].collidepoint(event.pos): 
                            self.temp_size = 8
                        elif '10x10' in self.buttons and self.buttons['10x10'].collidepoint(event.pos): 
                            self.temp_size = 10
                            
                        elif 'black' in self.buttons and self.buttons['black'].collidepoint(event.pos): 
                            self.temp_color = BLACK_PIECE
                        elif 'white' in self.buttons and self.buttons['white'].collidepoint(event.pos): 
                            self.temp_color = WHITE_PIECE
                            
                        for key, btn in self.buttons.items():
                            if key.startswith('chest_') and btn.collidepoint(event.pos):
                                self.temp_chests = int(key.split('_')[1])
                        
                        if 'proceed' in self.buttons and self.buttons['proceed'].collidepoint(event.pos):
                            self.state = MENU_DIFFICULTY if self.temp_mode == MODE_PVAI else PLAYING
                            if self.state == PLAYING: self.init_board()
                            
                    elif self.state == MENU_DIFFICULTY:
                        if 'easy' in self.buttons and self.buttons['easy'].collidepoint(event.pos):
                            self.temp_difficulty = DIFF_EASY; self.init_board(); self.state = PLAYING
                        elif 'medium' in self.buttons and self.buttons['medium'].collidepoint(event.pos):
                            self.temp_difficulty = DIFF_MEDIUM; self.init_board(); self.state = PLAYING
                        elif 'hard' in self.buttons and self.buttons['hard'].collidepoint(event.pos):
                            self.temp_difficulty = DIFF_HARD; self.init_board(); self.state = PLAYING

                    elif self.state == PLAYING:
                        if 'reboot' in self.buttons and self.buttons['reboot'].collidepoint(event.pos):
                            self.state = MENU_MODE
                        elif 'hint' in self.buttons and self.buttons['hint'].collidepoint(event.pos) and self.hint_count > 0 and self.current_turn == self.temp_color and not self.ai_thinking:
                            self.hint_count -= 1
                            temp_hint_engine = AIEngine(DIFF_HARD)
                            self.hint_move = temp_hint_engine.get_best_move(self, bypass_error=True)
                        else:
                            mx, my = event.pos
                            if my > BOARD_TOP_OFFSET and not self.ai_thinking:
                                if self.temp_mode == MODE_PVAI and self.current_turn != self.temp_color:
                                    continue
                                c = mx // self.cell_size
                                r = (my - BOARD_TOP_OFFSET) // self.cell_size
                                if 0 <= r < self.board_size and 0 <= c < self.board_size:
                                    valid = self.get_valid_moves(self.current_turn)
                                    if (r, c) in valid:
                                        self.hint_move = None
                                        
                                        self.board[r][c] = self.current_turn
                                        for fr, fc in valid[(r, c)]:
                                            self.board[fr][fc] = self.current_turn
                                            
                                        chest = False
                                        if (r, c) in self.chests:
                                            self.chests.remove((r, c))
                                            self.trigger_chest_effect()
                                            if self.ai_engine:
                                                self.ai_engine.reset_cache()
                                            chest = True
                                            
                                        if self.loss_pending > 0 and not chest:
                                            self.remove_random_piece(self.current_turn)
                                            self.loss_pending -= 1
                                            
                                        if self.extra_turn_active:
                                            self.extra_turn_active = False
                                            if not self.get_valid_moves(self.current_turn):
                                                self.next_turn()
                                        else:
                                            self.next_turn()
                                            
                                        if self.state == PLAYING and self.temp_mode == MODE_PVAI and self.current_turn != self.temp_color:
                                            self.schedule_ai_turn()
                                    else:
                                        if self.sfx_invalid:
                                            self.sfx_invalid.play()
                                            
                    elif self.state == GAME_OVER:
                        if 'replay' in self.buttons and self.buttons['replay'].collidepoint(event.pos): 
                            self.state = MENU_MODE
                        elif 'quit' in self.buttons and self.buttons['quit'].collidepoint(event.pos): 
                            pygame.quit()
                            sys.exit()
                        elif 'view_board' in self.buttons and self.buttons['view_board'].collidepoint(event.pos):
                            self.state = VIEWING_RESULT_BOARD
                            
                    elif self.state == VIEWING_RESULT_BOARD:
                        if 'view_result' in self.buttons and self.buttons['view_result'].collidepoint(event.pos):
                            self.state = GAME_OVER

            if self.state == PLAYING:
                if self.alert_timer > 0:
                    self.alert_timer -= 1
                if getattr(self, 'ai_skipped_timer', 0) > 0:
                    self.ai_skipped_timer -= 1
                    
                if self.ai_thinking and pygame.time.get_ticks() - self.ai_think_start >= self.ai_delay:
                    self.execute_ai_turn()

            if self.state == MENU_MODE: self.draw_menu_mode()
            elif self.state == MENU_CONFIGURE: self.draw_menu_configure()
            elif self.state == MENU_DIFFICULTY: self.draw_menu_difficulty()
            elif self.state == PLAYING or self.state == VIEWING_RESULT_BOARD: self.draw_board()
            elif self.state == GAME_OVER: self.draw_game_over()
            
            pygame.display.flip()
            clock.tick(60)

if __name__ == "__main__":
    app = EndfieldOthello()
    app.run()
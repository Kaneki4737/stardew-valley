import os
import pygame

# Directions
DIR_DOWN, DIR_LEFT, DIR_RIGHT, DIR_UP = 0, 1, 2, 3

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=150):
        super().__init__()
        self.speed = speed  # pixels per second

        # Load sprite sheets
        base = os.path.join(os.path.dirname(__file__), "..", "assets", "characters")
        self.idle_sheet = self.safe_load(os.path.join(base, "character_idle.png"))
        self.walk_sheet = self.safe_load(os.path.join(base, "character_walking.png"))

        # Frame setup
        self.frame_width = 64
        self.frame_height = 64
        self.anim_speed = 0.15  # seconds per frame

        # Extract frames
        self.idle_frames = self.load_idle_frames_columns(self.idle_sheet)
        self.walk_frames = self.load_walk_frames_columns(self.walk_sheet)

        self.image = self.idle_frames[DIR_DOWN][0]
        self.rect = self.image.get_rect(topleft=(x, y))

        # Movement and animation state
        self.vx = 0
        self.vy = 0
        self.facing = DIR_DOWN
        self.anim_time = 0
        self.current_frame = 0

        # Inventory
        self.inventory = None

    def safe_load(self, path):
        if os.path.exists(path):
            try:
                return pygame.image.load(path).convert_alpha()
            except Exception:
                pass
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        s.fill((255, 0, 255))  # magenta placeholder
        return s

    def load_frames(self, sheet):
        """Split sheet into 4 directions with multiple frames."""
        frames = []
        sheet_width, sheet_height = sheet.get_size()
        cols = sheet_width // self.frame_width
        rows = sheet_height // self.frame_height

        for r in range(rows):  # Each row = direction
            row_frames = []
            for c in range(cols):
                frame = sheet.subsurface(pygame.Rect(c * self.frame_width, r * self.frame_height,
                                                    self.frame_width, self.frame_height))
                row_frames.append(frame)
            frames.append(row_frames)
        return frames

    def load_walk_frames_columns(self, sheet):
        """
        The walking sheet is arranged as 4 rows x 4 columns where each column is a direction:
        col0=Up, col1=Right, col2=Down, col3=Left. Rows are animation frames.
        We must return frames ordered by engine direction indices: [Down, Left, Right, Up].
        """
        sheet_width, sheet_height = sheet.get_size()
        cols = max(1, sheet_width // self.frame_width)
        rows = max(1, sheet_height // self.frame_height)

        # Build grid [rows][cols]
        grid = []
        for r in range(rows):
            row_frames = []
            for c in range(cols):
                frame = sheet.subsurface(pygame.Rect(c * self.frame_width, r * self.frame_height,
                                                    self.frame_width, self.frame_height))
                row_frames.append(frame)
            grid.append(row_frames)

        # Extract columns as directions
        def column_frames(col_index):
            return [grid[r][col_index] for r in range(rows) if col_index < len(grid[r])]

        # Map columns to our DIR_* ordering
        # Given: col0=Up, col1=Right, col2=Down, col3=Left
        up_frames = column_frames(0)
        right_frames = column_frames(1)
        down_frames = column_frames(2)
        left_frames = column_frames(3)

        frames_by_dir = [
            down_frames,  # DIR_DOWN = 0
            left_frames,  # DIR_LEFT = 1
            right_frames, # DIR_RIGHT = 2
            up_frames     # DIR_UP = 3
        ]

        # Ensure there is at least one frame per direction
        for i in range(len(frames_by_dir)):
            if not frames_by_dir[i]:
                frames_by_dir[i] = [self.idle_frames[i][0] if self.idle_frames and i < len(self.idle_frames) else sheet]

        return frames_by_dir

    def load_idle_frames_columns(self, sheet):
        """
        Try to load idle frames as columns-as-directions (Up, Right, Down, Left) like walking.
        Falls back to row-based if not enough columns, and ensures 4 direction lists.
        """
        sheet_width, sheet_height = sheet.get_size()
        cols = max(1, sheet_width // self.frame_width)
        rows = max(1, sheet_height // self.frame_height)

        # Build grid [rows][cols]
        grid = []
        for r in range(rows):
            row_frames = []
            for c in range(cols):
                frame = sheet.subsurface(pygame.Rect(c * self.frame_width, r * self.frame_height,
                                                    self.frame_width, self.frame_height))
                row_frames.append(frame)
            grid.append(row_frames)

        frames_by_dir = [[], [], [], []]  # Down, Left, Right, Up

        if cols >= 4:
            # columns are directions: 0=Up,1=Right,2=Down,3=Left
            def column_frames(ci):
                return [grid[r][ci] for r in range(rows) if ci < len(grid[r])]
            up_frames = column_frames(0)
            right_frames = column_frames(1)
            down_frames = column_frames(2)
            left_frames = column_frames(3)
            frames_by_dir = [down_frames, left_frames, right_frames, up_frames]
        else:
            # fallback: use first row as frames for all directions
            base = grid[0] if rows >= 1 else [sheet]
            frames_by_dir = [base[:], base[:], base[:], base[:]]

        # Ensure at least one frame per direction
        for i in range(4):
            if not frames_by_dir[i]:
                frames_by_dir[i] = [grid[0][0] if rows and cols else sheet]

        return frames_by_dir

    def handle_input(self, keys, dt):
        vx = 0
        vy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            vx -= 1
            self.facing = DIR_LEFT
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            vx += 1
            self.facing = DIR_RIGHT
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            vy -= 1
            self.facing = DIR_UP
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            vy += 1
            self.facing = DIR_DOWN

        if vx != 0 and vy != 0:
            norm = 0.70710678
            self.vx = int(self.speed * vx * norm)
            self.vy = int(self.speed * vy * norm)
        else:
            self.vx = int(self.speed * vx)
            self.vy = int(self.speed * vy)

    def update(self, dt):
        # Movement
        self.rect.x += int(self.vx * dt)
        self.rect.y += int(self.vy * dt)

        # Animation
        moving = self.vx != 0 or self.vy != 0
        self.anim_time += dt
        if moving:
            if self.anim_time >= self.anim_speed:
                self.anim_time = 0
                self.current_frame = (self.current_frame + 1) % len(self.walk_frames[self.facing])
            self.image = self.walk_frames[self.facing][self.current_frame]
        else:
            self.current_frame = 0
            self.image = self.idle_frames[self.facing][0]

    def draw(self, surface, camera):
        surface.blit(self.image, camera.apply(self.rect))

    def interact(self, tilemap):
        px = self.rect.centerx
        py = self.rect.centery
        c, r = tilemap.world_to_tile(px, py)
        selected = None
        if self.inventory:
            selected = self.inventory.get_selected_item()

        # Accept seeds or direct crop items
        if selected:
            name = selected['name'] if isinstance(selected, dict) else str(selected)
            if name.endswith('_seed'):
                crop = name.replace('_seed', '')
                planted = tilemap.plant(c, r, crop)
                if planted and self.inventory:
                    self.inventory.consume_selected()
                    return "planted"
            elif name in ('carrot', 'tomato'):
                planted = tilemap.plant(c, r, name)
                if planted and self.inventory:
                    self.inventory.consume_selected()
                    return "planted"
        if tilemap.is_tillable(c, r):
            tilled = tilemap.till(c, r)
            return "tilled" if tilled else None
        return None

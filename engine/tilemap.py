import os
import pygame
from .crop import Crop

def get_asset_path(*parts):
    base_dir = os.path.dirname(os.path.dirname(__file__))  # one level up from engine
    return os.path.join(base_dir, "assets", *parts)


class TileMap:
    def __init__(self, world_w, world_h, tile_w=64, tile_h=64, predefined_map=None):
        self.world_w = int(world_w)
        self.world_h = int(world_h)
        self.tile_w = int(tile_w)
        self.tile_h = int(tile_h)

        self.cols = max(1, self.world_w // self.tile_w)
        self.rows = max(1, self.world_h // self.tile_h)

        def safe_load(path):
            if os.path.exists(path):
                try:
                    surf = pygame.image.load(path).convert_alpha()
                    return pygame.transform.smoothscale(surf, (self.tile_w, self.tile_h))
                except Exception:
                    pass
            # fallback (pink placeholder)
            s = pygame.Surface((self.tile_w, self.tile_h), pygame.SRCALPHA)
            s.fill((255, 0, 255))
            return s

        # load tile surfaces
        grass_dir = get_asset_path("environment", "grass")
        env_dir = get_asset_path("environment")
        flowers_dir = get_asset_path("environment", "flowers")

        self.tile_surfaces = {}
        self.tile_surfaces['grass'] = safe_load(os.path.join(grass_dir, "grass.png"))
        mapping = {
            'up': "up.png",
            'down': "down.png",
            'left': "left.png",
            'right': "right.png",
            'up_left': "up_left.png",
            'up_right': "up_right.png",
            'down_left': "down_left.png",
            'down_right': "down_right.png",
            'corner_northeast': "corner_northeast.png",
            'corner_northwest': "corner_northwest.png",
            'corner_southeast': "corner_southeast.png",
            'corner_south_west': "corner_south_west.png",
        }
        for k, fn in mapping.items():
            self.tile_surfaces[k] = safe_load(os.path.join(grass_dir, fn))

        # use dirt_tile.png as the visual for dirt (tilled soil)
        self.tile_surfaces['dirt'] = safe_load(os.path.join(env_dir, "dirt_tile.png"))
        self.tile_surfaces['tree'] = safe_load(os.path.join(env_dir, "tree.png"))

        if os.path.exists(flowers_dir):
            for fname in os.listdir(flowers_dir):
                key = "flower_" + os.path.splitext(fname)[0]
                self.tile_surfaces[key] = safe_load(os.path.join(flowers_dir, fname))

        # Create map
        if predefined_map:
            self.map = [list(row) for row in predefined_map]
        else:
            # Base grass only; no earth patches. Player can till tiles with Space.
            self.map = [['grass' for _ in range(self.cols)] for _ in range(self.rows)]

            # Border setup using grass-edge tiles
            for c in range(self.cols):
                self.map[0][c] = 'up'
                self.map[self.rows - 1][c] = 'down'
            for r in range(self.rows):
                self.map[r][0] = 'left'
                self.map[r][self.cols - 1] = 'right'
            self.map[0][0] = 'corner_northwest'
            self.map[0][self.cols - 1] = 'corner_northeast'
            self.map[self.rows - 1][0] = 'corner_south_west'
            self.map[self.rows - 1][self.cols - 1] = 'corner_southeast'

            # A couple of trees at fixed positions for scenery
            if self.rows > 6 and self.cols > 6:
                self.map[3][3] = 'tree'
                self.map[3][self.cols - 4] = 'tree'

        self.tilled = set()
        self.crops = pygame.sprite.Group()

    def tile_to_world(self, c, r):
        return c * self.tile_w, r * self.tile_h

    def world_to_tile(self, x, y):
        return int(x // self.tile_w), int(y // self.tile_h)

    def draw(self, surface, camera, highlight_pos=None):
        cam_rect = camera.world_view_rect()
        start_col = max(0, cam_rect.left // self.tile_w)
        end_col = min(self.cols, (cam_rect.right // self.tile_w) + 1)
        start_row = max(0, cam_rect.top // self.tile_h)
        end_row = min(self.rows, (cam_rect.bottom // self.tile_h) + 1)

        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                wx, wy = self.tile_to_world(c, r)
                dest = pygame.Rect(wx - cam_rect.left, wy - cam_rect.top, self.tile_w, self.tile_h)
                tile_type = self.map[r][c]

                # If this is a decorative overlay (tree/flower), draw grass first
                if tile_type == 'tree' or (isinstance(tile_type, str) and tile_type.startswith('flower_')):
                    base_grass = self.tile_surfaces.get('grass')
                    if base_grass:
                        surface.blit(base_grass, dest)
                    overlay = self.tile_surfaces.get(tile_type)
                    if overlay:
                        surface.blit(overlay, dest)
                else:
                    surf = self.tile_surfaces.get(tile_type, self.tile_surfaces.get('grass'))
                    surface.blit(surf, dest)

        # update and draw crops
        for crop in self.crops:
            crop.update()
            dest_rect = crop.rect.move(-cam_rect.left, -cam_rect.top)
            surface.blit(crop.image, dest_rect)

        # draw highlight
        if highlight_pos:
            hc, hr = highlight_pos
            if 0 <= hr < self.rows and 0 <= hc < self.cols:
                hx, hy = self.tile_to_world(hc, hr)
                rect = pygame.Rect(hx - cam_rect.left, hy - cam_rect.top, self.tile_w, self.tile_h)
                pygame.draw.rect(surface, (255, 255, 0), rect, 3)

    def is_tillable(self, c, r):
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return self.map[r][c].startswith('grass') or self.map[r][c].startswith('flower_')
        return False

    def till(self, c, r):
        if 0 <= r < self.rows and 0 <= c < self.cols and self.is_tillable(c, r):
            self.map[r][c] = 'dirt'
            self.tilled.add((c, r))
            return True
        return False

    def plant(self, c, r, crop_type):
        if (c, r) in self.tilled and not any((crop.rect.topleft == self.tile_to_world(c, r)) for crop in self.crops):
            wx, wy = self.tile_to_world(c, r)
            crop = Crop(wx, wy, crop_type, frame_w=self.tile_w // 2, frame_h=self.tile_h // 2)
            self.crops.add(crop)
            return True
        return False

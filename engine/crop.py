import os
import pygame

def get_asset_path(*parts):
    base_dir = os.path.dirname(os.path.dirname(__file__))  # one level up from engine
    return os.path.join(base_dir, "assets", *parts)

class Crop(pygame.sprite.Sprite):
    def __init__(self, x, y, crop_type, frame_w=32, frame_h=32):
        super().__init__()
        self.crop_type = crop_type
        self.growth_timer = 0
        self.stage = 0
        self.growth_speed = 120  # ticks per stage (simple)

        # Load combined growth sheet: 2 rows (tomato, carrot) x 3 columns (stages)
        sheet_path = get_asset_path("crop", "carrot_and_tomato.png")
        sheet = None
        if os.path.exists(sheet_path):
            try:
                sheet = pygame.image.load(sheet_path).convert_alpha()
            except Exception:
                sheet = None

        if sheet:
            w, h = sheet.get_size()
            cols = 3
            rows = 2
            cell_w = w // cols
            cell_h = h // rows

            # row 0 -> tomato, row 1 -> carrot
            row_index = 0 if crop_type == 'tomato' else 1
            frames = []
            for c in range(cols):
                sub = sheet.subsurface((c * cell_w, row_index * cell_h, cell_w, cell_h))
                surf = pygame.Surface((frame_w*2, frame_h*2), pygame.SRCALPHA)
                rect = sub.get_rect(center=(surf.get_width()//2, surf.get_height()//2))
                surf.blit(sub, rect)
                frames.append(surf)
            self.frames = frames
        else:
            # placeholder green rectangle
            surf = pygame.Surface((frame_w*2, frame_h*2), pygame.SRCALPHA)
            surf.fill((0,200,0))
            self.frames = [surf]

        self.image = self.frames[self.stage]
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self):
        self.growth_timer += 1
        if self.growth_timer >= self.growth_speed and self.stage < len(self.frames) - 1:
            self.stage += 1
            self.image = self.frames[self.stage]
            self.growth_timer = 0
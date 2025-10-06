import os
import pygame


def get_asset_path(*parts):
    base_dir = os.path.dirname(os.path.dirname(__file__))  # one level up from engine
    return os.path.join(base_dir, "assets", *parts)


class Inventory:
    def __init__(self, slot_count=8, slot_size=64):
        self.slot_count = slot_count
        self.slot_size = slot_size
        self.items = [None] * slot_count
        self.selected_index = 0

        # load inventory bar background (full bar)
        bar_path = get_asset_path("ui", "inventory_bar.png")
        self.bar_image = None
        if os.path.exists(bar_path):
            try:
                self.bar_image = pygame.image.load(bar_path).convert_alpha()
            except Exception:
                self.bar_image = None

        # per-slot fallback drawing surface if bar is missing
        self.slot_image = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
        self.slot_image.fill((200, 200, 200))

        # font for item count
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)

        # load item icons from combined crop inventory sprite
        self.item_icons = {}
        inv_icon_path = get_asset_path("crop", "carrot_and_tomato_for_inventory.png")
        if os.path.exists(inv_icon_path):
            try:
                sheet = pygame.image.load(inv_icon_path).convert_alpha()
                w, h = sheet.get_size()
                # assume two columns: carrot | tomato
                half = w // 2
                carrot_icon = sheet.subsurface((0, 0, half, h))
                tomato_icon = sheet.subsurface((half, 0, half, h))
                # scale icons to fit inside slot with padding
                pad = 8
                icon_w = max(8, self.slot_size - pad)
                icon_h = max(8, self.slot_size - pad)
                carrot_icon = pygame.transform.smoothscale(carrot_icon, (icon_w, icon_h))
                tomato_icon = pygame.transform.smoothscale(tomato_icon, (icon_w, icon_h))
                self.item_icons['carrot'] = carrot_icon
                self.item_icons['carrot_seed'] = carrot_icon
                self.item_icons['tomato'] = tomato_icon
                self.item_icons['tomato_seed'] = tomato_icon
            except Exception:
                pass

    def add_item(self, item_name, amount=1):
        for i, item in enumerate(self.items):
            if item and item['name'] == item_name:
                item['count'] += amount
                return True
        for i in range(len(self.items)):
            if self.items[i] is None:
                self.items[i] = {'name': item_name, 'count': amount}
                return True
        return False

    def remove_item(self, item_name, amount=1):
        for i, item in enumerate(self.items):
            if item and item['name'] == item_name:
                item['count'] -= amount
                if item['count'] <= 0:
                    self.items[i] = None
                return True
        return False

    def consume_selected(self, amount=1):
        selected = self.get_selected_item()
        if selected:
            return self.remove_item(selected['name'], amount)
        return False

    def select_next(self):
        self.selected_index = (self.selected_index + 1) % self.slot_count

    def select_previous(self):
        self.selected_index = (self.selected_index - 1) % self.slot_count

    def scroll(self, delta):
        if delta > 0:
            self.select_previous()
        elif delta < 0:
            self.select_next()

    def get_selected_item(self):
        return self.items[self.selected_index]

    def set_selected_index(self, index):
        if 0 <= index < self.slot_count:
            self.selected_index = index

    def draw(self, surface, screen_width, screen_height):
        bar_width_nominal = self.slot_count * self.slot_size
        # y_base will be computed after bar scaling so the bar sits at the bottom
        y_base = screen_height - int(self.slot_size * 1.2)

        scaled_bar = None
        scaled_bar_w = None
        scaled_bar_h = self.slot_size
        start_x = None

        # draw the inventory bar background if available, preserving aspect ratio by height ONLY
        if self.bar_image:
            try:
                bw, bh = self.bar_image.get_width(), self.bar_image.get_height()
                if bh > 0 and bw > 0:
                    # Choose a modest bar height tied to slot size so it stays near the bottom
                    target_bar_h = max(24, int(self.slot_size * 1.6))
                    scale = target_bar_h / bh
                    scaled_bar_h = max(1, int(bh * scale))
                    scaled_bar_w = max(1, int(bw * scale))
                    scaled_bar = pygame.transform.smoothscale(self.bar_image, (scaled_bar_w, scaled_bar_h))
                    start_x = (screen_width - scaled_bar_w) // 2
                    # place bar flush to bottom using its true height with a small margin
                    y_base = screen_height - scaled_bar_h - 6
                    surface.blit(scaled_bar, (start_x, y_base))
            except Exception:
                scaled_bar = None

        # fallback start_x if no bar or scaling failed
        if start_x is None:
            start_x = (screen_width - bar_width_nominal) // 2
            scaled_bar_w = bar_width_nominal
            # ensure the bar sits at the bottom even without a bar image
            y_base = screen_height - self.slot_size - 6

        # slot positioning: divide the bar width into equal cells per slot
        # distribute slots evenly across the visible bar width
        cell_w = max(self.slot_size, scaled_bar_w // self.slot_count)

        for i in range(self.slot_count):
            # center each slot rect within its cell; slot may shrink slightly to fit the bar
            cell_x = start_x + i * cell_w
            margin = max(6, self.slot_size // 12)
            slot_side = min(self.slot_size, cell_w - margin)
            x = cell_x + (cell_w - slot_side) // 2
            rect = pygame.Rect(x, y_base + (scaled_bar_h - slot_side) // 2 if scaled_bar else y_base, slot_side, slot_side)

            # draw per-slot fallback if no bar background
            if not scaled_bar:
                surface.blit(self.slot_image, rect)

            # highlight selected
            if i == self.selected_index:
                pygame.draw.rect(surface, (255, 255, 0), rect, 3)

            # draw item name and count
            if self.items[i]:
                item_name = self.items[i]['name']
                # draw icon if available, scaling to fit with padding inside actual slot rect
                icon = self.item_icons.get(item_name)
                if icon:
                    # scale icon to fit comfortably within the slot with padding
                    pad = max(10, slot_side // 10)
                    target_w = max(8, slot_side - pad)
                    target_h = max(8, slot_side - pad)
                    icon_scaled = pygame.transform.smoothscale(icon, (target_w, target_h))
                    icon_rect = icon_scaled.get_rect(center=(rect.centerx, rect.centery))
                    surface.blit(icon_scaled, icon_rect)
                else:
                    # fallback first-letter badge
                    name_text = self.font.render(item_name[0].upper(), True, (0, 0, 0))
                    surface.blit(name_text, (rect.left + 5, rect.top + 5))
                # omit numeric count rendering per request

import pygame

class Camera:
    """
    Camera(screen_w, screen_h, world_w, world_h)
    Provides apply(rect) -> rect translated to screen coordinates,
    update(target) centers camera on target and clamps to world bounds.
    """
    def __init__(self, screen_w, screen_h, world_w, world_h):
        self.screen_w = int(screen_w)
        self.screen_h = int(screen_h)
        self.world_w = int(world_w)
        self.world_h = int(world_h)
        self.rect = pygame.Rect(0, 0, self.screen_w, self.screen_h)

    @property
    def offset_x(self):
        return self.rect.left

    @property
    def offset_y(self):
        return self.rect.top

    def apply(self, rect):
        """Return a rect positioned for blitting to the screen."""
        return rect.move(-self.rect.left, -self.rect.top)

    def world_view_rect(self):
        return self.rect

    def update(self, target):
        """
        Center the camera on the target (sprite or rect-like).
        Accepts a sprite with .rect or a pygame.Rect.
        """
        if hasattr(target, "rect"):
            center = target.rect.center
        elif isinstance(target, pygame.Rect):
            center = target.center
        else:
            return

        self.rect.center = center

        # Clamp to world bounds
        self.rect.left = max(0, min(self.rect.left, self.world_w - self.rect.width))
        self.rect.top = max(0, min(self.rect.top, self.world_h - self.rect.height))

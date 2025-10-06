import pygame
import sys
from engine.tilemap import TileMap
from engine.camera import Camera
from engine.player import Player
from engine.inventory import Inventory

pygame.init()

def main():
    # Screen and world settings
    screen_width, screen_height = 800, 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Stardew Clone")

    clock = pygame.time.Clock()

    # World size
    world_width, world_height = 1600, 1600

    # Initialize game objects
    player = Player(100, 100)
    tilemap = TileMap(world_width, world_height)
    camera = Camera(screen_width, screen_height, world_width, world_height)

    # Inventory with seeds
    # 8 slots to match inventory_bar.png; enlarge slots for better visibility
    inventory = Inventory(slot_count=8, slot_size=96)
    # Start with seeds but hide numeric counts in UI
    inventory.add_item("carrot_seed", 5)
    inventory.add_item("tomato_seed", 5)
    player.inventory = inventory  # Link inventory to player

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_e:  # Interact with tile
                    player.interact(tilemap)
                elif event.key == pygame.K_p:  # Plant at player position using selected item
                    c, r = tilemap.world_to_tile(player.rect.centerx, player.rect.centery)
                    selected_item = inventory.get_selected_item()
                    if selected_item and selected_item.get('name', '').endswith('_seed'):
                        crop_name = selected_item['name'].replace('_seed', '')
                        if tilemap.plant(c, r, crop_name):
                            inventory.consume_selected(1)
                elif event.key == pygame.K_SPACE:  # Till at player position
                    c, r = tilemap.world_to_tile(player.rect.centerx, player.rect.centery)
                    tilemap.till(c, r)
                # number key handling is below in KEYDOWN block
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (1, 3):  # Left click: till / Right click: plant
                    mouse_x, mouse_y = event.pos
                    world_x = mouse_x + camera.rect.left
                    world_y = mouse_y + camera.rect.top
                    col, row = tilemap.world_to_tile(world_x, world_y)

                    do_plant = (event.button == 3) or (pygame.key.get_mods() & pygame.KMOD_SHIFT)
                    if do_plant:  # Plant
                        selected_item = inventory.get_selected_item()
                        if selected_item and selected_item.get('name', '').endswith('_seed'):
                            crop_name = selected_item['name'].replace('_seed', '')
                            planted = tilemap.plant(col, row, crop_name)
                            if planted:
                                inventory.consume_selected(1)
                    else:  # Till
                        tilemap.till(col, row)

            elif event.type == pygame.MOUSEWHEEL:
                inventory.scroll(event.y)
            elif event.type == pygame.KEYDOWN:
                # Number keys 1-9 to select inventory slots
                if pygame.K_1 <= event.key <= pygame.K_9:
                    inventory.set_selected_index(event.key - pygame.K_1)

        # Player input and movement
        keys = pygame.key.get_pressed()
        player.handle_input(keys, dt)  # ✅ Pass dt here

        # Update player with delta time
        player.update(dt)  # ✅ Updated for dt

        # Update camera to follow player
        camera.update(player.rect)

        # Draw everything
        screen.fill((50, 150, 50))
        tilemap.draw(screen, camera, highlight_pos=tilemap.world_to_tile(player.rect.centerx, player.rect.centery))
        player.draw(screen, camera)
        inventory.draw(screen, screen_width, screen_height)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

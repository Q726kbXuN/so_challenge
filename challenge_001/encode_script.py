#!/usr/bin/env python3

from PIL import Image
import base64
import pygame

SOURCE_IMAGE = "pacifier.png"
SCALE_IMAGE = [2, 4] # Number of pixels to skip
SOURCE_CODE = "baby_talk.py"

BASE64_BLOB = None
DISPLAY_GRID = None

def setup_data():
    global BASE64_BLOB, DISPLAY_GRID
    with open(SOURCE_CODE, "rt", encoding="utf-8", newline="") as f:
        data = f.read()
        data = data.replace("\r", "")
        data = data.encode("utf-8")
        data = base64.b64encode(data)
        data = data.decode("utf-8")
        BASE64_BLOB = data

    DISPLAY_GRID = []
    img = Image.open(SOURCE_IMAGE)
    for y in range(0, img.size[1], SCALE_IMAGE[1]):
        DISPLAY_GRID.append([])
        for x in range(0, img.size[0], SCALE_IMAGE[0]):
            pixel = img.getpixel((x, y))
            DISPLAY_GRID[-1].append(1 if (sum(pixel) / len(pixel) < 200) else 0)

    while sum(DISPLAY_GRID[0]) == 0 and sum(DISPLAY_GRID[1]) == 0:
        DISPLAY_GRID.pop(0)
    while sum(DISPLAY_GRID[-1]) == 0 and sum(DISPLAY_GRID[-2]) == 0:
        DISPLAY_GRID.pop(-1)
    while sum(x[0] for x in DISPLAY_GRID) == 0 and sum(x[1] for x in DISPLAY_GRID) == 0:
        DISPLAY_GRID = [x[1:] for x in DISPLAY_GRID]
    while sum(x[-1] for x in DISPLAY_GRID) == 0 and sum(x[-2] for x in DISPLAY_GRID) == 0:
        DISPLAY_GRID = [x[:-1] for x in DISPLAY_GRID]

def main():
    pygame.init()
    disp_width, disp_height = 1000, 800
    screen = pygame.display.set_mode((disp_width, disp_height))
    font = pygame.font.SysFont(None, 40)
    running = True
    pixel_size = 10
    mouse_down = False
    mouse_set_mode = 0
    setup_data()

    def get_xy(event):
        x, y = event.pos
        x //= pixel_size
        y //= pixel_size * 2
        x -= 2
        y -= 2
        return x, y
    def xy_to_pix(x, y):
        disp_x = (x + 2) * pixel_size
        disp_y = (y + 2) * pixel_size * 2
        return disp_x, disp_y

    while running:
        event = pygame.event.wait()
        if event.type == pygame.KEYDOWN:
            if event.key in {pygame.K_ESCAPE, pygame.K_q}:
                running = False
                break
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = get_xy(event)
            if 0 <= x < len(DISPLAY_GRID[0]) and 0 <= y < len(DISPLAY_GRID):
                mouse_set_mode = (DISPLAY_GRID[y][x] + 1) % 2
                print(mouse_set_mode, DISPLAY_GRID[y][x])
                mouse_down = True
                DISPLAY_GRID[y][x] = mouse_set_mode
        elif event.type == pygame.MOUSEBUTTONUP:
            mouse_down = False
        elif event.type == pygame.MOUSEMOTION:
            if mouse_down:
                x, y = get_xy(event)
                if 0 <= x < len(DISPLAY_GRID[0]) and 0 <= y < len(DISPLAY_GRID):
                    DISPLAY_GRID[y][x] = mouse_set_mode

        screen.fill((0, 0, 0))
        for y, row in enumerate(DISPLAY_GRID):
            for x, pixel in enumerate(row):
                if pixel == 1:
                    disp_x, disp_y = xy_to_pix(x, y)
                    pygame.draw.rect(screen, (200, 200, 200), (disp_x, disp_y, pixel_size, pixel_size * 2))

        total_active = sum(sum(x) for x in DISPLAY_GRID)
        if total_active == len(BASE64_BLOB):
            msg = "Correct number of pixels!"
        elif total_active > len(BASE64_BLOB):
            msg = f"{total_active - len(BASE64_BLOB)} too many!"
        else:
            msg = f"{len(BASE64_BLOB) - total_active} too few!"
        text = font.render(msg, True, (255, 255, 255))
        screen.blit(text, (50, 10))

        pygame.display.update()

    print("-" * 100)
    temp = list(BASE64_BLOB)
    for y, row in enumerate(DISPLAY_GRID):
        line = ""
        for x, pixel in enumerate(row):
            if pixel == 1:
                if len(temp) > 0:
                    line += temp.pop(0)
                else:
                    line += "#"
            else:
                line += " "
        print(line)
    print("-" * 100)
    if len(temp) > 0:
        print("".join(temp))
    print("-" * 100)

if __name__ == "__main__":
    main()

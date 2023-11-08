# -*- coding: utf-8 -*-
"""
Created on Wed Nov 8 07:01:15 2023

@author: Windows
"""

import pygame
import random
import heapq
import time

# Initialize Pygame
pygame.init()

# Define constants for screen dimensions and colors
SCREEN_WIDTH, SCREEN_HEIGHT = 820, 620
MAZE_WALL_COLOR = (0, 0, 255)
EXIT_COLOR = (0, 255, 0)
PACMAN_COLOR = (255, 255, 0)
DEBRIS_COLOR = (255, 0, 0)
WASTE_COLOR = (255, 165, 0)
BACKGROUND_COLOR = (0, 0, 0)
TILE_SIZE = 20
MAZE_DIMENSIONS = (SCREEN_WIDTH // TILE_SIZE, SCREEN_HEIGHT // TILE_SIZE)
FPS = 30
FONT = pygame.font.Font(None, 36)

# Generate the initial maze layout with borders and pattern
MAZE_LAYOUT = [[1 if i == 0 or i == MAZE_DIMENSIONS[1] - 1 or
                j == 0 or j == MAZE_DIMENSIONS[0] - 1 or
                (i % 2 == 0 and j % 2 == 0)
                else 0 for j in range(MAZE_DIMENSIONS[0])]
               for i in range(MAZE_DIMENSIONS[1])]

# Place exit in the maze
exit_position = (MAZE_DIMENSIONS[0] - 2, MAZE_DIMENSIONS[1] // 2)
MAZE_LAYOUT[exit_position[1]][exit_position[0]] = 0  # Ensure the exit is accessible

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# Define the A* pathfinding algorithm
def a_star_search(start, goal, graph):
    frontier = []
    heapq.heappush(frontier, (0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}
    
    while frontier:
        current = heapq.heappop(frontier)[1]
        
        if current == goal:
            break
        
        if current not in graph:  # Check if the current node is still in the graph
            continue  # Skip this iteration if the current node has been removed
        
        for next in graph[current]:
            new_cost = cost_so_far[current] + 1
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(goal, next)
                heapq.heappush(frontier, (priority, next))
                came_from[next] = current
    
    return came_from, cost_so_far

# Define the maze graph based on the layout
def make_graph(maze):
    graph = {}
    for y, row in enumerate(maze):
        for x, cell in enumerate(row):
            if cell == 0:  # If this is a path
                graph[(x, y)] = []
                if x > 0 and maze[y][x - 1] == 0:  # Left
                    graph[(x, y)].append((x - 1, y))
                if x < len(row) - 1 and maze[y][x + 1] == 0:  # Right
                    graph[(x, y)].append((x + 1, y))
                if y > 0 and maze[y - 1][x] == 0:  # Up
                    graph[(x, y)].append((x, y - 1))
                if y < len(maze) - 1 and maze[y + 1][x] == 0:  # Down
                    graph[(x, y)].append((x, y + 1))
            # Exclude hazardous tiles from the graph
            elif cell == 2:  # If this is a hazardous tile
                continue  # Do not include this tile in the graph
    return graph

class PacMan:
    def __init__(self, x, y, graph, maze_layout):
        self.x = x
        self.y = y
        self.graph = graph
        self.maze_layout = maze_layout
        self.path = []
        self.find_path()
        self.damage = 0
        self.emotional_state = "Neutral"
        self.start_time = time.time()
        self.found_exit = False
        self.hazard_memory = set()
    
    def find_path(self):
        start = (self.x // TILE_SIZE, self.y // TILE_SIZE)
        goal = exit_position
        came_from, _ = a_star_search(start, goal, self.graph)
        current = goal
        path = []
        while current != start:
            path.append(current)
            current = came_from.get(current)
            if current is None:
                break
        self.path = path[::-1]
    
    def move(self):
        if self.path:
            next_pos = self.path.pop(0)
            self.x, self.y = next_pos[0] * TILE_SIZE, next_pos[1] * TILE_SIZE
    
    def update(self, hazards, debris):
        current_tile = (self.x // TILE_SIZE, self.y // TILE_SIZE)
        if current_tile in hazards:
            self.emotional_state = "Fear"
            self.hazard_memory.add(current_tile)
            self.maze_layout[current_tile[1]][current_tile[0]] = 2
            self.reset_position()
        elif current_tile in debris:
            self.emotional_state = "Caution"
            self.hazard_memory.add(current_tile)
            self.maze_layout[current_tile[1]][current_tile[0]] = 2
            self.reset_position()
        else:
            self.emotional_state = "Neutral"
            self.move()
    
    def reset_position(self):
        self.x, self.y = TILE_SIZE, TILE_SIZE
        self.graph = make_graph(self.maze_layout)
        self.find_path()
    
    def draw(self, screen):
        pygame.draw.rect(screen, PACMAN_COLOR, (self.x, self.y, TILE_SIZE, TILE_SIZE))
    
    def get_time_damage(self):
        return time.time() - self.start_time, self.damage
    
    def at_exit(self):
        current_position = (self.x // TILE_SIZE, self.y // TILE_SIZE)
        return current_position == exit_position

class Game:
    def __init__(self):
        self.emotion_counter = {"Fear": 0, "Caution": 0, "Neutral": 0}
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.maze_graph = make_graph(MAZE_LAYOUT)
        self.pacman = PacMan(TILE_SIZE, TILE_SIZE, self.maze_graph, MAZE_LAYOUT)
        self.hazards = self.place_random_items(WASTE_COLOR, 3)
        self.debris = self.place_random_items(DEBRIS_COLOR, 3)

    def place_random_items(self, item_color, quantity):
        items = set()
        while len(items) < quantity:
            position = (random.randint(1, MAZE_DIMENSIONS[0] - 2), random.randint(1, MAZE_DIMENSIONS[1] - 2))
            if position != exit_position and MAZE_LAYOUT[position[1]][position[0]] == 0 and position not in items:
                items.add(position)
        return items

    def run(self):
        game_number = 0
        while game_number < 100 and self.running:
            game_start_time = time.time()
            exit_position = (MAZE_DIMENSIONS[0] - 2, random.randint(1, MAZE_DIMENSIONS[1] - 2))
            MAZE_LAYOUT[exit_position[1]][exit_position[0]] = 0
            self.hazards = self.place_random_items(WASTE_COLOR, 3)
            self.debris = self.place_random_items(DEBRIS_COLOR, 3)
            self.maze_graph = make_graph(MAZE_LAYOUT)
            self.pacman = PacMan(TILE_SIZE, TILE_SIZE, self.maze_graph, MAZE_LAYOUT)
            self.emotion_counter = {"Fear": 0, "Caution": 0, "Neutral": 0}

            while not self.pacman.at_exit() and self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False

                self.pacman.update(self.hazards, self.debris)
                self.emotion_counter[self.pacman.emotional_state] += 1
                self.draw()
                self.clock.tick(FPS)

            if self.running:
                time_taken = time.time() - game_start_time
                print(f"Game {game_number}: Time taken: {time_taken:.2f} seconds, Damage incurred: {self.pacman.damage}. "
                      f"Emotions Experienced: Fear({self.emotion_counter['Fear']}), "
                      f"Caution({self.emotion_counter['Caution']}), Neutral({self.emotion_counter['Neutral']})")
                game_number += 1

        pygame.quit()

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        for y, row in enumerate(MAZE_LAYOUT):
            for x, cell in enumerate(row):
                color = MAZE_WALL_COLOR if cell == 1 else BACKGROUND_COLOR
                if (x, y) == exit_position:
                    color = EXIT_COLOR
                pygame.draw.rect(self.screen, color, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        for hazard in self.hazards:
            pygame.draw.rect(self.screen, WASTE_COLOR, (hazard[0] * TILE_SIZE, hazard[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        for debris in self.debris:
            pygame.draw.rect(self.screen, DEBRIS_COLOR, (debris[0] * TILE_SIZE, debris[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        self.pacman.draw(self.screen)
        time_damage_text = FONT.render(f"Time: {int(self.pacman.get_time_damage()[0])}s Damage: {self.pacman.get_time_damage()[1]}", True, (255, 255, 255))
        self.screen.blit(time_damage_text, (5, 5))
        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()

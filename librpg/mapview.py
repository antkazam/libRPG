import pygame

from librpg.config import graphics_config as g_cfg
from librpg.tile import Tile
from librpg.locals import UP, RIGHT, DOWN, LEFT, ANIMATION_PERIOD, SRCALPHA
from librpg.color import BLACK
from librpg.virtualscreen import get_screen
from librpg.util import Position


class MapView(object):

    """
    map_model: MapModel (read-only)
    MapModel with the information to be drawn.

    screen: Surface (read-only)
    Screen surface to blit to.

    background: Surface (private)
    Surface containing the static terrain and scenario layers that are
    drawn at the lower level.

    foreground: Surface (private)
    Surface containing the static scenario tiles that are drawn at
    the upper level.

    camera_mode: CameraMode (private)
    CameraMode to calculate the map focus.
    """

    def __init__(self, map_model):
        self.map_model = map_model

        self.init_backgrounds()
        self.init_foreground()
        self.camera_mode = g_cfg.camera_mode
        self.camera_mode.attach_to_map(self.map_model)

        self.phase = 0

    def init_backgrounds(self):
        self.backgrounds = []
        for animation_phase in xrange(ANIMATION_PERIOD):
            self.backgrounds.append(self.init_background(animation_phase))

    def init_background(self, animation_phase):
        background_width = (g_cfg.tile_size * self.map_model.width +
                            g_cfg.screen_width)
        background_height = (g_cfg.tile_size * self.map_model.height +
                             g_cfg.screen_height)
        background = pygame.Surface((background_width, background_height))

        background.fill(BLACK)

        for y in xrange(self.map_model.height):
            for x in xrange(self.map_model.width):
                bg_x = (g_cfg.map_border_width
                        + x * g_cfg.tile_size)
                bg_y = (g_cfg.map_border_height
                        + y * g_cfg.tile_size)
                terrain_tile_surface = self.map_model.terrain_layer[x, y].\
                                       get_surface(animation_phase)
                background.blit(terrain_tile_surface, (bg_x, bg_y))

                for i in range(self.map_model.scenario_number):
                    scenario_tile = self.map_model.scenario_layer[i][x, y]
                    if scenario_tile.obstacle != Tile.ABOVE:
                        scenario_tile_surface = scenario_tile.get_surface()
                        background.blit(scenario_tile_surface, (bg_x, bg_y))
        return background

    def init_foreground(self):
        foreground_width = (g_cfg.tile_size * self.map_model.width
                            + g_cfg.screen_width)
        foreground_height = (g_cfg.tile_size * self.map_model.height
                             + g_cfg.screen_height)
        self.foreground = pygame.Surface((foreground_width, foreground_height),
                                         SRCALPHA, 32)

        for y in xrange(self.map_model.height):
            for x in xrange(self.map_model.width):
                for i in range(self.map_model.scenario_number):
                    scenario_tile = self.map_model.scenario_layer[i][x, y]
                    if scenario_tile.obstacle == Tile.ABOVE:
                        fg_x = (g_cfg.map_border_width
                                + x * g_cfg.tile_size)
                        fg_y = (g_cfg.map_border_height
                                + y * g_cfg.tile_size)
                        scenario_tile_surface = scenario_tile.get_surface()
                        self.foreground.blit(scenario_tile_surface,
                                             (fg_x, fg_y))

    def draw(self):
        party_avatar = self.map_model.party_avatar

        # Draw the background
        if party_avatar:
            party_pos = party_avatar.position
            movement_offset = self.calc_object_movement_offset(party_avatar)
            party_x_offset, party_y_offset = movement_offset
        else:
            party_pos = Position(0, 0)
            party_x_offset, party_y_offset = 0, 0
        self.bg_topleft = self.camera_mode.calc_bg_slice_topleft(
                                                            party_pos,
                                                            party_x_offset,
                                                            party_y_offset)
        bg_rect = pygame.Rect(self.bg_topleft, g_cfg.screen_dimensions)
        phase = self.phase / g_cfg.animation_frame_period
        get_screen().blit(self.backgrounds[phase], (0, 0), bg_rect)

        # Draw the map objects
        self.draw_object_layer(self.map_model.below_objects)
        self.draw_object_layer(self.map_model.obstacle_objects)
        self.draw_object_layer(self.map_model.above_objects)

        # Draw the foreground
        get_screen().blit(self.foreground, (0, 0), bg_rect)

        # Update phase
        self.phase = (self.phase + 1) % (ANIMATION_PERIOD
                                       * g_cfg.animation_frame_period)

    def draw_object_layer(self, object_layer):
        if g_cfg.object_width > g_cfg.tile_size or\
           g_cfg.object_height > g_cfg.tile_size:
            object_layer.sort(key=lambda x: x.position)

        for obj in object_layer:
            obj_x_offset, obj_y_offset = self.calc_object_movement_offset(obj)
            obj_topleft = self.camera_mode.\
                    calc_object_topleft(self.bg_topleft, obj.position,
                                        obj.image.width, obj.image.height,
                                        obj_x_offset, obj_y_offset)
            obj_rect = pygame.Rect(obj_topleft,
                                   g_cfg.object_dimensions)
            get_screen().blit(obj.get_surface(), obj_rect)

    def calc_object_movement_offset(self, obj):
        obj_x_offset, obj_y_offset = 0, 0
        if obj.movement_phase > 0:
            offset = obj.movement_phase * g_cfg.tile_size / obj.speed
            if not obj.going_back:
                if obj.facing == UP:
                    obj_y_offset = offset
                elif obj.facing == RIGHT:
                    obj_x_offset = - offset
                elif obj.facing == DOWN:
                    obj_y_offset = - offset
                elif obj.facing == LEFT:
                    obj_x_offset = offset
            else:
                if obj.facing == UP:
                    obj_y_offset = - offset
                elif obj.facing == RIGHT:
                    obj_x_offset = offset
                elif obj.facing == DOWN:
                    obj_y_offset = offset
                elif obj.facing == LEFT:
                    obj_x_offset = - offset
        return obj_x_offset, obj_y_offset

    def calc_pos_from_mouse(self, pos):
        scr_x, scr_y = pos
        x = int((scr_x + self.bg_topleft[0] - g_cfg.map_border_width)
                / g_cfg.tile_size)
        y = int((scr_y + self.bg_topleft[1] - g_cfg.map_border_height)
                / g_cfg.tile_size)
        return x, y

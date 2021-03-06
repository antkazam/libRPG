from librpg.world import World
from librpg.party import Character
from librpg.path import charset_path
from librpg.util import Position

from worldtest.mymaps import Map1, Map2, Map3

def char_factory(name):
    return Character('Andy', charset_path('naked_man.png'))

class MyWorld(World):

    def __init__(self, save_file=None):
        maps = {1: Map1, 2: Map2, 3: Map3}
        World.__init__(self, maps=maps, character_factory=char_factory)
        if save_file is None:
            self.initial_state(map=1, position=Position(5, 4), chars=['Andy'])
        else:
            self.load_state(state_file=save_file)

    def custom_gameover(self):
        print 'MyWorld.custom_gameover()'

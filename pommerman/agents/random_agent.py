'''An agent that preforms a random action each step'''
from . import BaseAgent
import numpy as np
from .. import constants
from .. import utility

STOP = 0
UP = 1
DOWN = 2
LEFT = 3
RIGHT = 4
BOMB = 5

##########
# B-tree #
##########
SUCCSESS = "SUCCSESS"
RUNNING = "RUNNING"
FAIL = "FAIL"
SEQUENCE = "SEQUENCE"
FALLBACK = "FALLBACK"

class Node():
  def __init__(self, func = None, status = None, typ = None, children = []):
    self.func = func
    self.status = status
    self.typ = typ
    self.children = children

  def tick(self):
    self.status=RUNNING
    if self.typ==FALLBACK:
      self.fallBack()
    if self.typ == SEQUENCE:
      self.sequence()
    if self.typ == None:
      s = self.func()
      if s == True:
        self.status=SUCCSESS
      else:
        self.status=FAIL

  def fallBack(self):
    for child in self.children:
      child.tick()
      if child.status==SUCCSESS:
        self.status=SUCCSESS
        return
    self.status=FAIL
    return

  def sequence(self):
    for child in self.children:
      child.tick()
      if child.status==FAIL:
        self.status=FAIL
        return
    self.status=SUCCSESS
    return

class RandomAgent(BaseAgent):
    """The Random Agent that returns random actions given an action_space."""
    def __init__(self, *args, **kwargs):
        super(RandomAgent, self).__init__(*args, **kwargs)
        self.root = Node(typ = FALLBACK)
        self.buildTree()

    def act(self, obs, action_space):
        self.collectObs(obs)
        #print(action_space)
        #print(obs['board'])
        #print(obs['bomb_blast_strength'])
        #print(obs['enemies'])

        #print(obs['blast_strength'])
        self.root.tick()
        valid_positions = self.getValidPositions()
        print(valid_positions)
        return self.action#LEFT#action_space.sample()

    ##########
  	# Build  #
  	##########
    def buildTree(self):
        #self.root = Node(typ = FALLBACK)
        self.root.children = [Node(typ = SEQUENCE),Node(typ = SEQUENCE),Node(func = self.right)]
        self.root.children[0].children =[Node(func = self.false), Node(func = self.stop)]
        self.root.children[1].children =[Node(func = self.true), Node(func = self.left)]

  	##############
  	# Tree Funcs #
  	##############

    def true(self):
        return True
    def false(self):
        return False
    def stop(self):
        self.action=STOP
        return True
    def left(self):
        self.action=LEFT
        return True
    def right(self):
        self.action=RIGHT

    ################
    # Helper funcs #
    ################
    
    def collectObs(self, obs):
        self.obs = obs
        self.my_position = tuple(obs['position'])
        self.board = np.array(obs['board'])
        self.bombs = self.convert_bombs(np.array(obs['bomb_blast_strength']))
        self.enemies = [constants.Item(e) for e in obs['enemies']]
        self.ammo = int(obs['ammo'])
        self.blast_strength = int(obs['blast_strength'])
        return

    def convert_bombs(self, bomb_map):
        '''Flatten outs the bomb array'''
        ret = []
        locations = np.where(bomb_map > 0)
        for r, c in zip(locations[0], locations[1]):
            ret.append({
                'position': (r, c),
                'blast_strength': int(bomb_map[(r, c)])
            })
        return ret

    def getValidPositions(self):
      # Choose a random but valid direction.
        directions = [
            constants.Action.Stop, constants.Action.Left,
            constants.Action.Right, constants.Action.Up, constants.Action.Down
        ]
        valid_directions = self._filter_invalid_directions(
            self.board,self.my_position, directions, self.enemies)
        return valid_directions


    ###############
    # Static func #
    ###############

    @staticmethod
    def _filter_invalid_directions(board, my_position, directions, enemies):
        ret = []
        for direction in directions:
            position = utility.get_next_position(my_position, direction)
            if utility.position_on_board(
                    board, position) and utility.position_is_passable(
                        board, position, enemies):
                ret.append(direction)
        return ret
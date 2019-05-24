'''An agent that preforms a random action each step'''
from . import BaseAgent
from collections import defaultdict
import queue
import random

import numpy as np
from .. import constants
from .. import utility

STOP = 0
UP = 1
DOWN = 2
LEFT = 3
RIGHT = 4
BOMB = 5
RANGE = 4

class RandomAgent(BaseAgent):
    """The Random Agent that returns random actions given an action_space."""
    def __init__(self, *args, **kwargs):
        super(RandomAgent, self).__init__(*args, **kwargs)
        self.bombs = None
        self.root = Node(typ = FALLBACK)
        self.action = STOP
        self.buildTree()

    def act(self, obs, action_space):
        self.collectObs(obs)
        #print(self.bombs)
        #print(self.dist)
        #for bomb in self.bombs:
        #  print(self.dist[(bomb['position'])])
        #print(self.items.get(constants.Item.Wood)) #get position of a square
        #print(self.blast_strength) 
        self.root.tick()
        return self.action#random.choice(validDir).value

    ##########
  	# Build  #
  	##########
    def buildTree(self):
        self.root.children = [Node(typ = SEQUENCE), Node(typ = SEQUENCE),Node(typ = SEQUENCE),Node(func = self.right)]
        self.root.children[0].children =[Node(func = self.isValidPosition), Node(func = self.goToClosestValid)]
        self.root.children[1].children =[Node(func = self.false), Node(func = self.stop)]
        self.root.children[2].children =[Node(func = self.true), Node(func = self.goNearestWall)]

  	##############
  	# Tree Funcs #
  	##############

    #check if we are in a position where a bomb can hit us
    def isValidPosition(self):
        invalidPos = self.getInValidPositions()
        if self.my_position in invalidPos:
          return False
        return True

    #go to closest safe position
    def goToClosestValid(self):
        self.goTo(self.getClosestValid())
        return True

    def bombIsNear(self):
        if self.bombs == []:
          return False
        else:
          return True

    def placeBomb(self):
        self.action = BOMB
        return True

    def goNearestWall(self):
        currentWall = None
        currentDist = 99
        for wall in self.items.get(constants.Item.Wood):
            thisDist = self._distance(wall,self.my_position)
            if thisDist < currentDist:
                currentDist = thisDist
                currentWall = wall
        if currentWall == None:
            return False
        self.goTo(currentWall)
        return True

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
        self.items, self.dist, self.prev = self._djikstra(
            self.board, self.my_position, self.bombs, self.enemies, depth=10)
        return

    def goTo(self,point):
        currentDist = self._distance(self.my_position,point)
        actions = self.getValidDirections()
        for action in actions:
            nextPosition = utility.get_next_position(self.my_position, action)
            thisDist = self._distance(nextPosition,point)
            if thisDist < currentDist:
                currentDist = thisDist
                self.action = action.value

    def convert_bombs(self, bomb_map):
        '''Flatten outs the bomb array'''
        ret = []

        '''Add previous bombs if life_left is above 0 and if the bomb is out of our obs range'''
        if self.bombs is not None:
          for bomb in self.bombs:
            if self._out_of_range(bomb['position'], self.my_position, 4):
              bomb['life_left'] -= 1
              if bomb['life_left'] > 0:
                print("bomb out range ", bomb)
                ret.append(bomb)
          
        locations = np.where(bomb_map > 0)
        for r, c in zip(locations[0], locations[1]):
            ret.append({
                'position': (r, c),
                'blast_strength': int(bomb_map[(r, c)]),
                'life_left': int(self.obs['bomb_life'][(r,c)])
            })
        return ret

    def getValidDirections(self):
        directions = [
            constants.Action.Stop, constants.Action.Left,
            constants.Action.Right, constants.Action.Up, constants.Action.Down
        ]
        valid_directions = self._filter_invalid_directions(
            self.board,self.my_position, directions, self.enemies)
        return valid_directions

    def getClosestValid(self):
        closestDist = 99
        closestPos = None
        valid_positions = self.getValidPositions()
        for position in valid_positions:
          thisDist = self._distance(position,self.my_position)
          if thisDist < closestDist:
            currentDist = closestDist
            closestPos = position
        return closestPos

    def getValidPositions(self):
        ret = []

        invalidPos = self.getInValidPositions()
        locations = np.where(self.board != 5)
        for r, c in zip(locations[0], locations[1]):
            position = (r,c)
            if utility.position_on_board(
                    self.board, position) and utility.position_is_passable(
                        self.board, self.position, self.enemies) and position not in invalidPos:
                ret.append(position)
        return ret

    def getInValidPositions(self):
        deadlyPositions = []
        for bomb in self.bombs:
          for i in range(0,bomb['blast_strength']):
            x,y = bomb['position']
            deadlyPositions.append((x+i,y))
            deadlyPositions.append((x-i,y))
            deadlyPositions.append((x,y+i))
            deadlyPositions.append((x,y-i))
        return deadlyPositions

    ###############
    # Static func #
    ###############

    @staticmethod
    def _distance(p_1,p_2):
        x_1, y_1 = p_1
        x_2, y_2 = p_2
        return abs(x_1 - x_2) + abs(y_1 - y_2)

    @staticmethod
    def _out_of_range(p_1, p_2, depth):
        '''Determines if two points are out of rang of each other'''
        x_1, y_1 = p_1
        x_2, y_2 = p_2
        return abs(y_2 - y_1) > depth or abs(x_2 - x_1) > depth

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

    @staticmethod
    def _djikstra(board, my_position, bombs, enemies, depth=None, exclude=None):
        assert (depth is not None)

        if exclude is None:
            exclude = [
                constants.Item.Fog, constants.Item.Rigid, constants.Item.Flames
            ]

        def out_of_range(p_1, p_2):
            '''Determines if two points are out of rang of each other'''
            x_1, y_1 = p_1
            x_2, y_2 = p_2
            return abs(y_2 - y_1) + abs(x_2 - x_1) > depth

        items = defaultdict(list)
        dist = {}
        prev = {}
        Q = queue.Queue()

        my_x, my_y = my_position
        for r in range(max(0, my_x - depth), min(len(board), my_x + depth)):
            for c in range(max(0, my_y - depth), min(len(board), my_y + depth)):
                position = (r, c)
                if any([
                        out_of_range(my_position, position),
                        utility.position_in_items(board, position, exclude),
                ]):
                    continue

                prev[position] = None
                item = constants.Item(board[position])
                items[item].append(position)
                
                if position == my_position:
                    Q.put(position)
                    dist[position] = 0
                else:
                    dist[position] = np.inf


        for bomb in bombs:
            if bomb['position'] == my_position:
                items[constants.Item.Bomb].append(my_position)

        while not Q.empty():
            position = Q.get()

            if utility.position_is_passable(board, position, enemies):
                x, y = position
                val = dist[(x, y)] + 1
                for row, col in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    new_position = (row + x, col + y)
                    if new_position not in dist:
                        continue

                    if val < dist[new_position]:
                        dist[new_position] = val
                        prev[new_position] = position
                        Q.put(new_position)
                    elif (val == dist[new_position] and random.random() < .5):
                        dist[new_position] = val
                        prev[new_position] = position   


        return items, dist, prev


############################################################################
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



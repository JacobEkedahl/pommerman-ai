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
        self.my_bombs = []        
        self._recently_visited_positions = []
        self._recently_visited_length = 1
        self.target_powerup = None
        self.buildTree()

    def act(self, obs, action_space):
        self.collectObs(obs) #has to before tick
        self.root.tick()
        self.updateVisited() #has to be after tick
        return self.action

    ##########
    # Build  #
    ##########
    def buildTree(self):
        self.root.children = [Node(typ = SEQUENCE), Node(typ = SEQUENCE),Node(typ = SEQUENCE),Node(typ = SEQUENCE),Node(typ = SEQUENCE)]

        self.root.children[0].children = [Node(func = self.isInvalidPosition), Node(typ = FALLBACK)]
        self.root.children[1].children = [Node(func = self.isNearToEnemy), Node(func = self.canPlaceBombs), Node(func = self.placeBomb)]
        self.root.children[2].children = [Node(func = self.needsPowerUp), Node(typ = FALLBACK)]
        self.root.children[3].children = [Node(func = self.observingEnemy) , Node(func=self.goNearEnemy)]
        self.root.children[4].children = [Node(func = self.random)]

        self.root.children[0].children[1].children = [Node(func = self.goToSafestValid), Node(typ = SEQUENCE)]
        self.root.children[0].children[1].children[1].children = [Node(func = self.canKick), Node(func = self.kickBomb)]

        self.root.children[2].children[1].children = [Node(typ = SEQUENCE), Node(typ = SEQUENCE), Node(typ=SEQUENCE)]
        self.root.children[2].children[1].children[0].children = [Node(func = self.powerUpNearAndReachable), Node(func = self.goNearestPowerUp)]
        self.root.children[2].children[1].children[1].children = [Node(func = self.isCloseToWall), Node(func = self.canPlaceBombs), Node(func = self.placeBomb)]
        self.root.children[2].children[1].children[2].children = [Node(func = self.goNearestWall)]

    ##############
    # Tree Funcs #
    ##############

    #simple and bad attack
    def isNearToEnemy(self):
        for enemie in self.enemies:
            pos = self.items.get(enemie)
            if pos == None:
                continue
            if self.dist[pos[0]] <= 2:
                #print("will attack: ", enemie, ", my friend is: ", self.teammate)
                return True
        return False

    def kickBomb(self):
        print("kickBomb")
        for bomb in self.bombs:
            x, y = bomb['position']
            if (self.board[max(x-1,0)][y] in [0,4,10,11,12,13] and self.board[min(x+1,10)][y] in [0,4,10,11,12,13]) or (self.board[x][max(y-1,0)] in [0,4,10,11,12,13] and self.board[x][min(y+1,10)] in [0,4,10,11,12,13]):
                self.goTo(bomb['position'])
                return True
        return True

    def canPlaceBombs(self):
        return self.ammo > 0

    def random(self):
        valid_actions = self.getValidDirections(self.my_position)
        if not valid_actions:
            print("RANDOM STOP")
            self.action = STOP
            return
        self.action = random.choice(valid_actions).value
        print("RANDOM", self.action)
        return True

    def observingEnemy(self):
        positions = []
        for enemie in self.enemies:
            pos = self.items.get(enemie)
            if pos != None:
                positions.append(pos[0])
        if positions == []:
            return False
        return True

    def canKick(self):
        return self.obs['can_kick']

    def goNearEnemy(self):
        print("goNearEnemy")
        for enemie in self.enemies:
            pos = self.items.get(enemie)
            if pos != None:
                self.goTo(pos[0])
        return True
    
    def needsPowerUp(self):
        if self.obs['can_kick'] == True and self.ammo > 1:
            return False
        return True

    def powerUpNearAndReachable(self):
        self.target_powerup = None
        extraBomb = self.items.get(constants.Item.ExtraBomb)
        incrRange = self.items.get(constants.Item.IncrRange)
        kick = self.items.get(constants.Item.Kick)

        valid_targets = []
        if not self.canKick():
            if kick != None:
                for k in kick:
                    if (self.dist[k]) != np.inf:
                        valid_targets.append(k)
        if incrRange != None  and not valid_targets:
            for iR in incrRange:
                if (self.dist[iR]) != np.inf:
                    valid_targets.append(iR)
        if extraBomb != None and not valid_targets:
            for eB in extraBomb:
                if (self.dist[eB]) != np.inf:
                    valid_targets.append(eB)
        if self.canKick() and not valid_targets and kick != None:                
            for k in kick:
                if (self.dist[k]) != np.inf:
                    valid_targets.append(k)

        
        if valid_targets:
            self.setTargetPowerUp(valid_targets)
            return True
        else:
            return False

    def goNearestPowerUp(self):
        #print("goNearestPowerUp")
        self.goTo(self.target_powerup)
        return True

    def isCloseToWall(self):
        if self.items.get(constants.Item.Wood) == None:
            return False
        for wall in self.items.get(constants.Item.Wood):
            if self._distance(wall,self.my_position) == 1:
                return True
        return False

    #check if we are in a position where a bomb can hit us
    def isInvalidPosition(self):
        invalidPos = self.getInValidPositions(self.bombs)
        if self.my_position in invalidPos:
          #print("IM IN WRONG POS", self.bombs)
          return True

        #print("IM IN RIGHT POS", invalidPos, self.bombs)
        return False

    #go to closest safe position
    def goToSafestValid(self):
        print("goToSafestValid")
        point = self.getSafestValid()
        if point == None:
            return False
        self.escape(point)
        return True

    def placeBomb(self):
        print("placeBomb")
        x, y = self.my_position
        for position in self.items.get(constants.Item.Passage):
            if self.dist[position] == np.inf:
                continue

            # We can reach a passage that's outside of the bomb strength.
            if self.dist[position] > self.blast_strength:
                self.action = BOMB
                return True

            # We can reach a passage that's outside of the bomb scope.
            position_x, position_y = position
            if position_x != x and position_y != y:
                self.action = BOMB
                return True
        return False

    def goNearestWall(self):
        print("goNearestWall")
        currentWall = None
        currentDist = 99
        walls = self.items.get(constants.Item.Wood)
        if walls == None:
            return False
        for wall in walls:
            thisDist = self._distance(wall,self.my_position)
            if thisDist < currentDist and (self.dist[wall]) != np.inf:
                currentDist = thisDist
                currentWall = wall
        if currentWall == None:
            return False
        self.goTo(currentWall)
        return True

    ################
    # Helper funcs #
    ################

    def collectObs(self, obs):
        self.obs = obs
        self.my_position = tuple(obs['position'])
        self.board = np.array(obs['board'])
        self.bombs = self.convert_bombs(np.array(obs['bomb_blast_strength']))
        self.message = obs['message']
        self.teammate = obs['teammate']
        self.players = [constants.Item(e) for e in obs['enemies']]
        self.enemies = [e for e in self.players if (e != self.teammate or e != constants.Item.AgentDummy)]
        self.blast_strength = int(obs['blast_strength'])
        self.items, self.dist, self.prev = self._djikstra(
            self.board, self.my_position, self.bombs, self.players, self.obs['can_kick'], depth=10)
        #print("msg: ", self.message, ", teammate: " , self.teammate, ", enemies: ", self.enemies)
        self.updateMyBombs()
        return

    def getNextPositionToTarget(self, position):
        target_pos = None

        if position not in self.dist or self.dist[position] is np.inf:
            closestDist = 99
            for pos in self.dist:
                if self.dist[pos] is not np.inf:
                    dist = self._distance(pos, position)
                    #print("pos: ", pos, ", dist: ", dist)
                    if dist < closestDist:
                        closestDist = dist
                        target_pos = pos
        else:
            target_pos = position

        res = target_pos
        while target_pos != self.my_position:
            if target_pos != self.my_position:
                res = target_pos
            target_pos = self.prev[target_pos]

        return res

    def setTargetPowerUp(self, targets):
        currentDist = 99

        for target in targets:
            dist = self.dist[target]
            if dist < currentDist:
                currentDist = dist
                self.target_powerup = target

    def updateVisited(self):
        # Add this position to the recently visited uninteresting positions so we don't return immediately.
        self._recently_visited_positions.append(self.my_position)
        self._recently_visited_positions = self._recently_visited_positions[
            -self._recently_visited_length:]
        return

    def addBomb(self):
        self.my_bombs.append({
          'life_left': constants.DEFAULT_BOMB_LIFE
        })

    def updateMyBombs(self):
        for bomb in self.my_bombs:
          bomb['life_left'] -= 1
          if bomb['life_left'] == 0:
            self.my_bombs.remove(bomb)

    def goTo(self,point):
        nextPos = self.getNextPositionToTarget(point)
        if self.will_it_explode(nextPos) or self.dist[nextPos] == np.inf:
            self.random()
            return
        nextMove = utility.get_direction(self.my_position, nextPos)
        self.action = nextMove.value

    def escape(self, point):
        nextPos = self.getNextPositionToTarget(point)
        '''
        will next position guarantee kill me?
        if my currentposition will kill me, go to any safe square next move, else stay put
        '''
        if self.will_it_explode(nextPos):
            if not self.will_it_explode(self.my_position):
                self.action = STOP
                return
            else:
                my_actions = self.getValidDirections(self.my_position)
                for action in my_actions:
                    possible_pos = utility.get_next_position(self.my_position, action)
                    if not self.will_it_explode(possible_pos):
                        self.action = action
                        return

        nextMove = utility.get_direction(self.my_position, nextPos)
        self.action = nextMove.value

    def will_it_explode(self, point):
        for bomb in self.bombs:
            if bomb['life_left'] <= 1:
                deadly_positions = self.getInvalidPosition_frombomb(bomb)
                if point in deadly_positions:
                    return True

    def get_non_valid_positions(self):
        ret = []
        for bomb in self.bombs:
            if bomb['life_left'] <= 1:
                ret.extend(self.getInvalidPosition_frombomb(bomb))

        return ret

    def convert_bombs(self, bomb_map):
        '''Flatten outs the bomb array'''
        ret = []

        '''Add previous bombs if life_left is above 0 and if the bomb is out of our obs range'''
        if self.bombs is not None:
          for bomb in self.bombs:
            if self._out_of_range(bomb['position'], self.my_position, 4):
              bomb['life_left'] -= 1
              if bomb['life_left'] > 0:
                ret.append(bomb)
          
        locations = np.where(bomb_map > 0)
        for r, c in zip(locations[0], locations[1]):
            ret.append({
                'position': (r, c),
                'blast_strength': int(bomb_map[(r, c)]),
                'life_left': int(self.obs['bomb_life'][(r,c)])
            })
        return ret

    def getValidDirections(self,pos):
        directions = [
            constants.Action.Stop, constants.Action.Left,
            constants.Action.Right, constants.Action.Up, constants.Action.Down
        ]
        valid_directions = self._filter_invalid_directions(
            self.board,pos, directions, self.players, self.get_non_valid_positions())

        valid_directions = self._filter_recently_visited(
            valid_directions, self.my_position, self._recently_visited_positions)

        return valid_directions

    def getSafestValid(self):
        closestDist = 99
        closestPos = None
        valid_positions = self.getValidPositions()
        for position in valid_positions:
          thisDist = self.dist[position]
          if thisDist < closestDist:
            closestDist = thisDist
            closestPos = position

        #print("clostestPos: ", closestPos, " my pos: ", self.my_position, " no valid: ", len(valid_positions))
        return closestPos

    def getValidPositions(self):
        ret = []

        invalidPos = self.getInValidPositions(self.bombs)
        locations = []
        for position in self.dist:
            if self.dist[position] != np.inf:
                if utility.position_on_board(
                        self.board, position) and utility.position_is_passable(
                            self.board, position, self.players) and position not in invalidPos:
                    ret.append(position)
        return ret

    def life_left(self, position):
        return ""

    def getInvalidPosition_frombomb(self, bomb):
        deadlyPositions = []
        for i in range(0,bomb['blast_strength']):
            x,y = bomb['position']
            life_left = bomb['life_left']
            deadlyPositions.append((x+i,y))
            deadlyPositions.append((x-i,y))
            deadlyPositions.append((x,y+i))
            deadlyPositions.append((x,y-i))
            deadlyPositions.append((x,y))
        return deadlyPositions


    def getInValidPositions(self, bombs):
        deadlyPositions = []
        for bomb in bombs:
            deadlyPositions.extend(self.getInvalidPosition_frombomb(bomb))

        for pos in self.dist:
            if self.dist[pos] == np.inf and pos not in deadlyPositions:
                deadlyPositions.append(pos)
                
        return deadlyPositions

    ###############
    # Static func #
    ###############


    @staticmethod
    def _has_bomb(obs):
        return obs['ammo'] >= 1

    @staticmethod
    def _distance(p_1,p_2):
        if p_1 == None or p_2 == None:
            return 99
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
    def _filter_invalid_directions(board, my_position, directions, enemies, deadly_positions):
        ret = []
        for direction in directions:
            position = utility.get_next_position(my_position, direction)
            if position in deadly_positions:
                print("DIRECTION ", direction, " not valid position")
            if utility.position_on_board(
                    board, position) and utility.position_is_passable(
                        board, position, enemies) and position not in deadly_positions and not utility.position_is_flames(board, position):
                ret.append(direction)
        return ret


    @staticmethod
    def _filter_recently_visited(directions, my_position,
                                 recently_visited_positions):
        ret = []
        for direction in directions:
            if not utility.get_next_position(
                    my_position, direction) in recently_visited_positions:
                ret.append(direction)

        if not ret:
            ret = directions
        return ret

    @staticmethod
    def _djikstra(board, my_position, bombs, enemies, can_kick, depth=None, exclude=None):
        if depth is None:
            depth = 10

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



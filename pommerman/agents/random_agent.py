'''An agent that preforms a random action each step'''
from . import BaseAgent

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

    def act(self, obs, action_space):
        #print(action_space)
        #print(obs['board'])
        #print(obs['bomb_blast_strength'])
        #print(obs['enemies'])
        #print(obs['ammo'])
        #print(obs['blast_strength'])
        self.root = Node(typ = FALLBACK)
        self.buildTree()
        self.root.tick()
        return self.action#LEFT#action_space.sample()

    ##########
	# Build  #
	##########
    def buildTree(self):
        #self.root = Node(typ = FALLBACK)
        self.root.children = [Node(typ = SEQUENCE),Node(typ = SEQUENCE),Node(func = self.right)]

        self.root.children[0].children =[Node(func = self.false), Node(func = self.stop)]
        self.root.children[1].children =[Node(func = self.true), Node(func = self.left)]


	##########
	# Funcs  #
	##########

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

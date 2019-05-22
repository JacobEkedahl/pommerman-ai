'''An agent that preforms a random action each step'''
from . import BaseAgent

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
    #print self.func
    #print self.typ
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
      #print child.status
      if child.status==SUCCSESS:
        self.status=SUCCSESS
        return
    self.status=FAIL
    return

  def sequence(self):
    for child in self.children:
      child.tick()
      #print child.status
      if child.status==FAIL:
        self.status=FAIL
        return
    self.status=SUCCSESS
    return

root = Node(typ = FALLBACK)

class RandomAgent(BaseAgent):
    """The Random Agent that returns random actions given an action_space."""

    def act(self, obs, action_space):
        #print(action_space.sample())
        #print(obs['board'])
        #print(obs['bomb_blast_strength'])
        print(obs['enemies'])
        return action_space.sample()

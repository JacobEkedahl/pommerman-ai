'''An agent that preforms a random action each step'''
from . import BaseAgent


class RandomAgent(BaseAgent):
    """The Random Agent that returns random actions given an action_space."""

    def act(self, obs, action_space):
        #print(action_space.sample())
        #print(obs['board'])
        #print(obs['bomb_blast_strength'])
        print(obs['enemies'])
        return action_space.sample()

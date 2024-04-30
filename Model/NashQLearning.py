import numpy as np
import pygambit as pg
import ipywidgets as widgets
from IPython.display import display
from History import History
from Environment import Environment, Game

class QTable:
    def __init__(self, environment: Environment) -> None:
        self.table = {}
        for game in environment.getGames():
            shape = [game.getPossibleActions()[player] for player in range(environment.NPlayers)]  # Number of actions for each player
            shape.append(environment.NPlayers)  # Number of players
            self.table[environment.getGameIndex(game)] = np.zeros(shape, dtype=float)

    def getQTable(self):
        return self.table
    
    def getQvalue(self, state: Game, player: int, actions):
        return self.table[state][actions, player]

    def updateQvalue(self, state: Game, player: int, actions, alfa: float, gamma: float, nextQval, reward):
        self.table[state][actions, player] = (1 - alfa) * self.table[state][actions, player] + alfa * (reward + gamma * nextQval)

    def convertToTable(self):
        converted = []
        for game in self.table.keys():
            converted.append(self.table[game].copy())

        return np.array(converted)


        
class Agent:
    def __init__(self,number: int, environment: Environment) -> None:
        self.QTable = QTable(environment)
        self.environment = environment
        self.number = number
        self.currentAction = None
        self.currentStrategy = None
        

    def setCurrentStrategy(self, strategy: np.array):
        self.currentStrategy = strategy

    def __getPossibleActions(self, state: Game):
        return state.getPossibleActions()[self.number]

    def getQtable(self, state: Game):
        return self.QTable.getQTable()[self.environment.getGameIndex(state)]
    
    def Qtable(self):
        return self.QTable

    def QtableForHistory(self):
        return self.QTable.convertToTable()
    
    def chooseAction(self, epsilon: float):
        self.currentAction = np.random.choice(self.__getPossibleActions(self.environment.getCurrentGame()), p=self.currentStrategy) if np.random.rand() > epsilon else np.random.choice(self.__getPossibleActions(self.environment.getCurrentGame()))

class NashQLearning:
    def __init__(self, environment: Environment, goal_state = None, startingState = None) -> None:
        
        self.env  = environment
        self.agents = [Agent(i, environment) for i in range(environment.NPlayers)]
        
        self.goal_state = goal_state 
        
        self.__already_seen_equilibria = {}

        self.episodes = 1

        if startingState != None:
            self.startingState = startingState

        #decide strategy for nash equilibria computation
        if environment.NPlayers == 2:
            self.computeNashEq = self.twoPlNashEq
            self.updateQTable = self.updateQTable2
        elif environment.NPlayers == 3:
            self.computeNashEq = self.threePlNashEq
            self.updateQTable = self.updateQTable3
        elif environment.NPlayers == 4:
            self.computeNashEq = self.fourPlNashEq
            self.updateQTable = self.updateQTable4
        else:
            Exception("The number of players must be 2, 3 or 4")
       
        #widget
        self.gamesLoadingBarNashQ = widgets.IntProgress(
        value=0,
        min=0,
        max=self.episodes-1,
        step=1,
        description='Games:',
        bar_style='info',
        ) 
        display(self.gamesLoadingBarNashQ)

    #NashQ learning algorithm for n players
    def nashQlearning(self, alfa, gamma, epsilon, pure_training_ep, decaying_epsilon, reset = False):
        n_players = self.env.NPlayers
        
        
        #initialize values to display
        totalReward = [np.zeros(n_players) for _ in range(n_players)]
        diffs = [[]for _ in range(n_players)]
        NashQRewards = [[]for _ in range(n_players)]
        history = History()

        for t in range(self.episodes):
            history_element = History()        

            alfa = alfa / (t + 1 - pure_training_ep) if t >= pure_training_ep else alfa
            epsilon = epsilon / (t + 1 - decaying_epsilon) if t >= decaying_epsilon else epsilon

            #choose action for every player
            for agent in self.agents:
                agent.chooseAction(epsilon)

            actionProfile = tuple([agent.currentAction for agent in self.agents])

            #calculating next state and memorizing its
            r = self.env.reward(actionProfile)
            nextState = self.env.getNextState(actionProfile)
            currentState = self.env.getCurrentGame()
    
            
            for agent in self.agents:

                #compute the expected payoff for the next state
                next_NashEq = self.computeNashEq(nextState, agent.Qtable())
                
                next_qVal = self.getNextQVal(agent.Qtable(), nextState, next_NashEq)    
                
                #copy modified Qvalues
                oldQ = self.copyQTable(agent.Qtable(), currentState, actionProfile)
                
                #update qTable
                self.updateQTable(agent.Qtable(), actionProfile, alfa, gamma, r, next_qVal)
                
                #memorize the new qTable
                history_element.add(('Q'+str(agent.number)), agent.QtableForHistory())#.copy())
                
                #memorize the difference between the old and the new value in the qTable
                diffs[agent.number].append(self.diffQTable(agent.getQtable(currentState), oldQ, actionProfile))
                
                #update the total reward of the player i
                totalReward[agent.number] += r
                #memorize the reward of the player i
                NashQRewards[agent.number].append(r)
            

            #memorize the state
            history_element.add('current_state', currentState)
            #add the history element to the history
            history.add(t+1, history_element)

            #update the state
            if(reset and self.goal_state != None and currentState==self.goal_state):
                nextState = self.startingState
            
            self.playMove(nextState)

            #update the loading bar
            self.gamesLoadingBarNashQ.value += 1
        return totalReward, diffs, NashQRewards, history
            
    #setter for the number of players
    def setEpisodes(self, episodes):
        self.episodes = episodes
        self.gamesLoadingBarNashQ.max = episodes-1

    def playMove(self, nextState: Game)->None:
        self.env.setNextState(nextState)
        return
    
    def qTable_to_tuple(self, qTable:np.array):
        try:
            return tuple(self.qTable_to_tuple(subarray) for subarray in qTable)
        except TypeError:
            return qTable

    def getKey(self, state: Game, table: np.array):
        s = self.env.getGameIndex(state)
        t = self.qTable_to_tuple(table)
        return (s, t)
    
    def twoPlNashEq(self, state: Game, qTable: QTable):

        payoff_matrix = qTable.getQTable()[self.env.getGameIndex(state)]
        #if the equilibrium has already been computed return it
        if self.getKey(state, payoff_matrix) in self.__already_seen_equilibria.keys():
            return self.__already_seen_equilibria[self.getKey(state, payoff_matrix)]
        
        game = pg.Game.from_arrays(payoff_matrix[:,:,0], payoff_matrix[:,:,1], title=("gambe number"+str(state)))
        #compute the Nash Equilibrium
        eq = pg.nash.enummixed_solve(game).equilibria
        #normalize the equilibrium
        eq = eq[0].normalize()
        #convert the Nash Equilibrium to an array
        e = []
        for i in range(self.env.NPlayers):
            x = np.zeros(state.getPossibleActions()[i])
            e.append(x)
        e = np.zeros(np.shape(e))        
        
        for i in range(self.env.NPlayers):
            for j in range(self.env.getCurrentGame().getPossibleActions()[i]):
                e[i][j] = (float(eq[str(i+1)][str(j+1)]))
        
        self.__already_seen_equilibria[self.getKey(state, payoff_matrix)] = e
        
        return e

    def threePlNashEq(self, state: Game, qTable: QTable):
        payoff_matrix = qTable.getQTable()[self.env.getGameIndex(state)]
        #if the equilibrium has already been computed return it
        if self.getKey(state, payoff_matrix) in self.__already_seen_equilibria.keys():
            return self.__already_seen_equilibria[self.getKey(state, payoff_matrix)]
    
        state = self.env.getCurrentGame()      
        game = pg.Game.from_arrays(payoff_matrix[:,:,:,0], payoff_matrix[:,:,:,1], payoff_matrix[:,:,:,2], title=("gambe number"+str(state)))
        #compute the Nash Equilibrium
        eq = pg.nash.logit_solve(game).equilibria
        #normalize the equilibrium
        eq = eq[0].normalize()
        #convert the Nash Equilibrium to an array
        #e = np.zeros(tuple(state.getPossibleActions()))
        #e = np.zeros(tuple(self.env.getCurrentGame().getPossibleActions()))
        e = []
        for i in range(self.env.NPlayers):
            x = np.zeros(state.getPossibleActions()[i])
            e.append(x)
        e = np.zeros(np.shape(e))

        for i in range(self.env.NPlayers):
            for j in range(self.env.getCurrentGame().getPossibleActions()[i]):
                e[i][j] = (float(eq[str(i+1)][str(j+1)]))

        self.__already_seen_equilibria[self.getKey(state, payoff_matrix)] = e
        
        return e

    def fourPlNashEq(self, state: Game, qTable: QTable):
        payoff_matrix = qTable.getQTable()[self.env.getGameIndex(state)]     
        if self.getKey(state, payoff_matrix) in self.__already_seen_equilibria.keys():
            return self.__already_seen_equilibria[self.getKey(state, payoff_matrix)]
        
        state = self.env.getCurrentGame()
        game = pg.Game.from_arrays(payoff_matrix[state,:,:,0], payoff_matrix[state,:,:,1], payoff_matrix[state,:,:,2], payoff_matrix[state,:,:,3], title=("gambe number"+str(state)))
        #compute the Nash Equilibrium
        eq = pg.nash.logit_solve(game).equilibria
        #normalize the equilibrium
        eq = eq[0].normalize()
        #convert the Nash Equilibrium to an array
        e = []
        for i in range(self.env.NPlayers):
            x = np.zeros(state.getPossibleActions()[i])
            e.append(x)
        e = np.zeros(np.shape(e))

        for i in range(self.env.NPlayers):
            for j in range(self.env.getCurrentGame().getPossibleActions()[i]):
                e[i][j] = (float(eq[str(i+1)][str(j+1)]))
    
        self.__already_seen_equilibria[self.getKey(state, payoff_matrix)] = e
        
        return e

    #getting reward for a given state and actions, the arguments must be 
    #reward_matrix, state, player1_action, player2_action, player3_action(optional)
    def reward(self, state, player_actions, reward_matrix):
        if self.n_players == 2:
            return reward_matrix[state, player_actions[0], player_actions[1]]
        elif self.n_players == 3:
            return reward_matrix[state, player_actions[0], player_actions[1], player_actions[2]]
        elif self.n_players == 4:
            return reward_matrix[state, player_actions[0], player_actions[1], player_actions[2], player_actions[3]]
        else:
            Exception("The number of players must be 2, 3 or 4")
    
    #getting the expected payoff in the future state the arguments must be
    #player1_strategy, player2_strategy, payoff_matrix
    def expectedPayoff(self, payoff_matrix, player_strategies):
        if self.env.NPlayers == 2:
            return np.dot(player_strategies[0], np.dot(payoff_matrix, player_strategies[1]))
        elif self.env.NPlayers == 3:
            return np.dot(player_strategies[0], np.dot(player_strategies[1], np.dot(payoff_matrix, player_strategies[2])))
        elif self.env.NPlayers == 4:
            return np.dot(player_strategies[0], np.dot(player_strategies[1], np.dot(player_strategies[2], np.dot(payoff_matrix, player_strategies[3]))))
        else:
            Exception("The number of players must be 2, 3 or 4")

    #getting the expected payoff in the future state for n players
    def getNextQVal(self, qTable: QTable, next_state: Game, strategies: np.array):
        qTable = qTable.getQTable()
        next_qVal = np.zeros(self.env.NPlayers)
        for x in range(self.env.NPlayers):
            if self.env.NPlayers == 2:
                next_qVal[x] = self.expectedPayoff(qTable[self.env.getGameIndex(next_state)][ :, :, x], strategies)
            elif self.env.NPlayers == 3:
                next_qVal[x] = self.expectedPayoff(qTable[self.env.getGameIndex(next_state)][ :, :, :, x], strategies)
            elif self.env.NPlayers == 4:    
                next_qVal[x] = self.expectedPayoff(qTable[self.env.getGameIndex(next_state)][ :, :, :, :, x], strategies)
            else:
                Exception("The number of players must be 2, 3 or 4")
        return next_qVal
    
    #return a copy of the qTable in the state "state"
    def copyQTable(self, qTable: QTable, state: Game, actions):
        qTable = qTable.getQTable()
        if self.env.NPlayers > 4:
            raise Exception("The number of players must be 2, 3 or 4")
        return qTable[self.env.getGameIndex(state)][tuple(actions)].copy()


    #state must be dereferenced earlier than the other dimensions, being the qtable a dictionary qtable[state][...]...
    def updateQTable2(self, qTable: QTable, actions: np.array, alfa: float, gamma: float, r: np.array, next_qVal: np.array):
        state = self.env.getCurrentGame()
        qTable = qTable.getQTable()
        for x in range(self.env.NPlayers):
            qTable[self.env.getGameIndex(state)][ actions[0], actions[1], x] = (1 - alfa) * qTable[self.env.getGameIndex(state)][ actions[0], actions[1], x] + alfa * (r[x] + gamma * next_qVal[x])

    def updateQTable3(self, qTable: QTable, actions: np.array, alfa: float, gamma: float, r: np.array, next_qVal: np.array):
        state = self.env.getCurrentGame()
        qTable = qTable.getQTable()
        for x in range(self.env.NPlayers):
            qTable[self.env.getGameIndex(state)][ actions[0], actions[1], actions[2], x] = (1 - alfa) * qTable[self.env.getGameIndex(state)][ actions[0], actions[1], actions[2], x] + alfa * (r[x] + gamma * next_qVal[x])

    def updateQTable4(self, qTable: QTable, actions: np.array, alfa: float, gamma: float, r: np.array, next_qVal: np.array):
        state = self.env.getCurrentGame()
        qTable = qTable.getQTable()
        for x in range(self.env.NPlayers):
            qTable[self.env.getGameIndex(state)][ actions[0], actions[1], actions[2], actions[3], x] = (1 - alfa) * qTable[self.env.getGameIndex(state)][ actions[0], actions[1], actions[2], actions[3], x] + alfa * (r[x] + gamma * next_qVal[x])


    #returns the difference between the two qTables
    def diffQTable(self, newTable: np.array, oldTable: np.array, actions: np.array):
        if self.env.NPlayers > 4:
            raise Exception("The number of players must be 2, 3 or 4")
        return newTable[tuple(actions)] - oldTable
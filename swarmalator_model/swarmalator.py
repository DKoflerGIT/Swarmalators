import random as rnd
import math
import numpy as np


class Swarmalator:
    def __init__(self, id: int, num_swarmalators: int, memory_init: str):
        '''
        Instanciates a swarmalator object and initializes their memory.

        Parameters
        ----------
        id : int
            Time step of an iteration.
        num_swarmalators : float
            Number of swarmalators in the simulation.
        memory_init : {'random', 'zeroes'}
            Method of swarmalator memory initialization. `rand` (random positions and phases) `zero` (initialize positions and phases as 0)
        '''
        self.id = id
        self.num_swarmalators = num_swarmalators
        self.velocity = np.ones(2)
        self.phase_change = 0
        self.memory_init = memory_init
        self.init_memory()
    
    def init_memory(self):
        '''
        Initializes swarmalator memory.

        Parameters
        ----------
        memory_init : {'random', 'zeroes'}
            Method of swarmalator memory initialization. `rand` (random positions and phases) `zero` (initialize positions and phases as 0)
        '''
        if self.memory_init == 'zeroes' or self.memory_init == 'gradual':
            # initialize memories with zeros
            self.memory = np.zeros((self.num_swarmalators, 3)) #position-phase-array
            # initialize own position and phase randomly
            self.memory[self.id][0] = rnd.random() * 2.0 - 1.0
            self.memory[self.id][1] = rnd.random() * 2.0 - 1.0
            self.memory[self.id][2] = rnd.uniform(-math.pi, math.pi)
            
        elif self.memory_init == 'random':
            # initialize memorywith random values
            memory_positions = np.random.rand(self.num_swarmalators, 2) * 2.0 - 1.0 #position-array
            memory_phases = np.random.rand(self.num_swarmalators) * 2.0 * math.pi - math.pi #phase-vector
            memory_phases = memory_phases.reshape((self.num_swarmalators, 1))
            self.memory = np.concatenate((memory_positions, memory_phases), axis=1)

    def run(self, env_memory, env_velocities, delta_t: float, J: float, K: float, coupling_probability: float):
        '''
        Makes the swarmalator sync and swarm.

        Parameters
        ----------
        env_memory : np.ndarray[np.float64]
            Environment memory used to synchronize the swarmalator memory.
        env_velocities : np.ndarray[np.float64]
            Environment memory of velocities used to update it.
        delta_t : float
            Time step of an iteration.
        J : float
            Phase attraction strength. For J>0 swarmalators with similar phases attract each other. For J<0 opposite phased swarmalators are attracted.
        K : float
            Phase coupling strength. For K>0 swarmalators try to minimize their phase difference. For K<0 the difference is maximized.
        coupling_probability : float
            Probability that a swarmalator successfully receives information about another swarmalators position and phase.
        '''
        self.scan(env_memory, coupling_probability)
        self.think(J, K)
        self.move(delta_t)
        self.yell(env_memory, env_velocities)

    def scan(self, env_memory, coupling_probability: float):
        '''
        The swarmalator synchronizes its memory with the environment memory using a coupling probability.

        Parameters
        ----------
        memory : np.ndarray[np.float64]
            Environment memory used to synchronize the swarmalator memory.
        coupling_probability : float
            Probability that a swarmalator successfully receives information about another swarmalators position and phase.
        '''
        for i in range(self.num_swarmalators):
            if i != self.id:
                r = rnd.random()
                if r <= coupling_probability:
                    self.memory[i] = env_memory[i]

    def think(self, J: float, K: float):
        '''
        The swarmalator computes its velocity and phase change based on information about other swarmalators stored in its memory.

        Parameters
        ----------
        J : float
            Phase attraction strength. For J>0 swarmalators with similar phases attract each other. For J<0 opposite phased swarmalators are attracted.
        K : float
            Phase coupling strength. For K>0 swarmalators try to minimize their phase difference. For K<0 the difference is maximized.
        '''
        temp_mem = self.memory.copy()
        temp_mem = np.delete(temp_mem, self.id, axis=0)
        if self.memory_init == 'gradual': temp_mem = temp_mem[~np.all(temp_mem == 0, axis=1)]
        n = len(temp_mem)
        if n == 0: return

        # compute all x_j - x_i
        delta_pos = temp_mem[:, :2] - self.memory[self.id][:2]

        # compute all theta_j - theta_i
        delta_pha = temp_mem[:, 2] - self.memory[self.id][2]
        delta_pha = delta_pha.reshape((n, 1))

        # comute all |x_j - x_i|
        norms = np.linalg.norm(delta_pos, axis=1).reshape((n, 1))

        # compute all x_i' summands
        velocity_vals = delta_pos / norms * ((1.0 + J * np.cos(delta_pha)) - 1.0 / norms)

        # compute all theta_i' summands
        phase_change_vals = np.sin(delta_pha) / norms

        self.velocity = np.sum(velocity_vals, axis=0) / n
        self.phase_change = np.sum(phase_change_vals, axis=0) * K / n

    def move(self, delta_t: float):
        '''
        The swarmalator uses its current velocity and phase change information to move.

        Parameters
        ----------
        delta_t : float
            Time step of an iteration.
        '''
        self.memory[self.id][:2] = self.memory[self.id][:2]  + self.velocity * delta_t # compute and set new position

        p = self.memory[self.id][2] + self.phase_change * delta_t
        if p > math.pi: p -= 2 * math.pi
        if p < -math.pi: p += 2 * math.pi
        self.memory[self.id][2] = p # compute and set new phase
    
    def yell(self, env_memory, env_velocities):
        '''
        The swarmalator communicates its current position, phase and velocity to the environment.

        Parameters
        ----------
        env_memory : np.ndarray[np.float64]
            Environment memory of positions and phases to be updated.
        env_velocities : np.ndarray[np.float64]
            Environment memory of velocities to be updated.
        '''
        env_memory[self.id] = self.memory[self.id]
        env_velocities[self.id] = self.velocity
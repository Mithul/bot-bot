"""
This modules implements the bulk of Bot Evolution.
"""

import numpy as np
import copy
import settings
from utility import seq_is_equal, distance_between, angle_is_between, find_angle
from neural_network import NNetwork, sigmoid, softmax
import random
np.random.seed()
RED = (255,0,0)
GREEN = (0,255,0)
class Population:
    """
    The environment of bots and food.
    """

    def __init__(self, size, mutation_rate, no_food):
        assert(size >= 5)
        assert(0 < mutation_rate < 1)
        self.SIZE = size
        self.mutation_rate = mutation_rate
        self.bots = []
        self.food = []
        self.time_since_last_death = 0.0

        # The neural network will have 1 neuron in the input layer, 1 hidden
        # layer with 2 neurons, and 4 neurons in the output layer. The sigmoid
        # activation function will be used on the hidden layer, and a softmax
        # activation function will be used on the output layer. Input consists
        # of the bot's direction and if there is or isn't food in the bots field
        # of vision. Output consists of whether or not to move foward, turn
        # left, turn right, or do nothing.
        for i in range(size):
            # random_rgb = (np.random.randint(30, 256), np.random.randint(30, 256), np.random.randint(30, 256))
            self.bots.append(Bot(NNetwork((2, 2, 4), (sigmoid, softmax)), RED, self))

        for i in range(size):
            # random_rgb = (np.random.randint(30, 256), np.random.randint(30, 256), np.random.randint(30, 256))
            self.bots.append(Bot(NNetwork((2, 2, 4), (sigmoid, softmax)), GREEN, self))

        for i in range(no_food):
            self.food.append(Food(self))

    def eliminate(self, bot, replace = False):
        self.time_since_last_death = 0.0
        self.bots.remove(bot)
        if replace:
            # random_rgb = (np.random.randint(30, 256), np.random.randint(30, 256), np.random.randint(30, 256))
            self.bots.append(Bot(NNetwork((2, 2, 4), (sigmoid, softmax)), bot.RGB, self))

    def create_herbibots(self):
        for i in range(5):
            self.bots.append(Bot(NNetwork((2, 2, 4), (sigmoid, softmax)), GREEN, self))

    def create_carnibots(self):
        for i in range(5):
            self.bots.append(Bot(NNetwork((2, 2, 4), (sigmoid, softmax)), RED, self))

    def feed(self, bot, food, is_bot = False):
        # bot.score = 1.0
        # self.food.remove(food)
        # self.food.append(Food(self))
        # print "Feeding..."
        bot.score += 1.0
        if not is_bot:
            self.food.remove(food)
            self.food.append(Food(self))
        else:
            self.bots.remove(food)
        
        num_to_replace = int(self.SIZE / 7 - 1)
        if num_to_replace < 2:
            num_to_replace = 2
        for i in range(num_to_replace):
            weakest = self.bots[0]
            for other in self.bots:
                if other.score < weakest.score:
                    weakest = other
            self.eliminate(weakest)
        for i in range(num_to_replace):
            if np.random.uniform(0, 1) <= self.mutation_rate:
                # new_rgb = [bot.RGB[0], bot.RGB[1], bot.RGB[2]]
                new_rgb = random.choice([RED, GREEN])
                new_bot = Bot(bot.nnet, new_rgb, self)
                new_bot.x = bot.x + Bot.HITBOX_RADIUS * 4 * np.random.uniform(0, 1) * np.random.choice((-1, 1))
                new_bot.y = bot.y + Bot.HITBOX_RADIUS * 4 * np.random.uniform(0, 1) * np.random.choice((-1, 1))
                nb_c = new_bot.nnet.connections
                mutated = False
                while not mutated:
                    for k in range(len(nb_c)):
                        for i in range(nb_c[k].FROM.SIZE):
                            for j in range(nb_c[k].TO.SIZE):
                                if np.random.uniform(0, 1) <= self.mutation_rate:
                                    nb_c[k].weights[i][j] = nb_c[k].weights[i][j] * np.random.normal(1, 0.5) + np.random.standard_normal()
                                    mutated = True
                self.bots.append(new_bot)
            else:
                new_bot = Bot(bot.nnet, bot.RGB, self)
                new_bot.x = bot.x + Bot.HITBOX_RADIUS * 4 * np.random.uniform(0, 1) * np.random.choice((-1, 1))
                new_bot.y = bot.y + Bot.HITBOX_RADIUS * 4 * np.random.uniform(0, 1) * np.random.choice((-1, 1))
                self.bots.append(new_bot)

    def update(self, dt):
        """
        Updates the population's internals. The bulk of event handling for all
        bots and food starts here.
        """
        self.time_since_last_death += 1.0 / settings.FPS * dt * settings.TIME_MULTIPLIER

        for food in self.food[:]:
            if food not in self.food:
                continue
            food.update(dt)

        for bot in self.bots[:]:
            if bot not in self.bots:
                continue

            # sensory_input = []

            # # This is where the bot's field of vision is put into action.
            # min_theta = bot.theta - Bot.FIELD_OF_VISION_THETA / 2
            # max_theta = bot.theta + Bot.FIELD_OF_VISION_THETA / 2
            # food_in_sight = False
            # for food in self.food:
            #     if angle_is_between(find_angle(bot.x, bot.y, food.x, food.y), min_theta, max_theta):
            #         food_in_sight = True
            #         break
            # if food_in_sight:
            #     sensory_input.append(1.0)
            # else:
            #     sensory_input.append(0.0)

            # # Useful debugging outputs.
            # #print(bot.RGB)
            # #print(sensory_input)

            # bot.update(dt, sensory_input)

            sensory_input = []
            sensory_input_h = []
            chased = False
            chased_bot = None
                
            # This is where the bot's field of vision is put into action.
            min_theta = bot.theta - Bot.FIELD_OF_VISION_THETA / 2
            max_theta = bot.theta + Bot.FIELD_OF_VISION_THETA / 2
            food_in_sight = False
            
            # food in front
            if bot.RGB == GREEN:
                for food in self.food:
                    if angle_is_between(find_angle(bot.x, bot.y, food.x, food.y), min_theta, max_theta):
                        food_in_sight = True
                        break
                if food_in_sight:
                    sensory_input_h.append(1.0)
                else:
                    sensory_input_h.append(0.0)
                
                for bbot in self.bots:
                    if bbot.RGB == RED and angle_is_between(find_angle(bot.x, bot.y, bbot.x, bbot.y), min_theta, max_theta):
                        chased = True
                        chased_bot = bot
                        break
                if not chased:
                    sensory_input_h.append(0.0)
                elif chased:
                    sensory_input_h.append(1.0)

                
            # bot in front
            elif bot.RGB == RED:
                food_in_sight = False
                # version1 - check if bot in sight - eat that if it's there! :P
                idx = self.bots.index(bot)
                for bbot in self.bots:
                    if bbot.RGB == GREEN  and angle_is_between(find_angle(bot.x, bot.y, bbot.x, bbot.y), min_theta, max_theta):
                        food_in_sight = True
                        chased = True
                        chased_bot = bbot
                        break
                if food_in_sight:
                    # pdb.set_trace()
                    sensory_input.append(1.0)
                else:
                    sensory_input.append(0.0)

                sensory_input.append(0.0)

            if chased and bot.RGB == RED:
                for food in self.food:
                    if angle_is_between(find_angle(chased_bot.x, chased_bot.y, food.x, food.y), min_theta, max_theta):
                        food_in_sight = True
                        break
                if food_in_sight:
                    sensory_input_h = [1.0, 1.0]
                else:
                    sensory_input_h = [0.0, 1.0]

                chased_bot.update(dt, sensory_input_h)

            # Useful debugging outputs.
            #print(bot.RGB)
            #print(sensory_input)

            if bot.RGB == RED:
                bot.update(dt, sensory_input)
            elif bot.RGB == GREEN:
                bot.update(dt, sensory_input_h)


        if self.time_since_last_death >= 5:
            weakest = self.bots[0]
            for bot in self.bots:
                if bot.score < weakest.score:
                    weakest = bot
            self.eliminate(weakest, replace = True)

class Bot:
    """
    The representation of the circle thing with probes.
    """

    # In pixels/pixels per second/revolutions per second/radians.
    SPAWN_RADIUS = int(settings.WINDOW_WIDTH / 20) if settings.WINDOW_WIDTH <= settings.WINDOW_HEIGHT else int(settings.WINDOW_HEIGHT / 20)
    HITBOX_RADIUS = 6
    SPEED = 150.0
    TURN_RATE = 2 * np.pi
    FIELD_OF_VISION_THETA = 45 * np.pi / 180

    # These lists represent the output from the neural network. Note that the
    # output '[0, 0, 0, 1]' means "do nothing".
    MOVE_FORWARD =  [1, 0, 0, 0]
    TURN_LEFT =     [0, 1, 0, 0]
    TURN_RIGHT =    [0, 0, 1, 0]
    MOVE_FASTER =    [0, 0, 0, 1]

    def __init__(self, nnet, rgb, population):
        self.nnet = copy.deepcopy(nnet)
        self.RGB = rgb
        self.pop = population
        self.theta = np.random.uniform(0, 1) * 2 * np.pi
        self.x = settings.WINDOW_WIDTH / 2.0 + Bot.SPAWN_RADIUS * np.random.uniform(0, 1) * np.cos(self.theta)
        self.y = settings.WINDOW_HEIGHT / 2.0 + Bot.SPAWN_RADIUS * np.random.uniform(0, 1) * np.sin(self.theta)
        self.score = 0.0

    def _move_forward(self, dt):
        speed = Bot.SPEED if self.RGB == RED else Bot.SPEED * 0.9
        self.x += Bot.SPEED / settings.FPS * dt * np.cos(self.theta) * settings.TIME_MULTIPLIER
        self.y -= Bot.SPEED / settings.FPS * dt * np.sin(self.theta) * settings.TIME_MULTIPLIER
        if self.x < -Bot.HITBOX_RADIUS * 6 or self.x > settings.WINDOW_WIDTH + Bot.HITBOX_RADIUS * 6 \
        or self.y < -Bot.HITBOX_RADIUS * 6 or self.y > settings.WINDOW_HEIGHT + Bot.HITBOX_RADIUS * 6:
            self.pop.eliminate(self, replace = True)

    def _move_faster(self, dt):
        self.x += Bot.SPEED / settings.FPS * dt * np.cos(self.theta) * settings.TIME_MULTIPLIER
        self.y -= Bot.SPEED / settings.FPS * dt * np.sin(self.theta) * settings.TIME_MULTIPLIER
        if self.x < -Bot.HITBOX_RADIUS * 6 or self.x > settings.WINDOW_WIDTH + Bot.HITBOX_RADIUS * 6 \
        or self.y < -Bot.HITBOX_RADIUS * 6 or self.y > settings.WINDOW_HEIGHT + Bot.HITBOX_RADIUS * 6:
            self.pop.eliminate(self, replace = True)

    def _turn_left(self, dt):
        self.theta += Bot.TURN_RATE / settings.FPS * dt * settings.TIME_MULTIPLIER
        while self.theta >= 2 * np.pi:
            self.theta -= 2 * np.pi

    def _turn_right(self, dt):
        self.theta -= Bot.TURN_RATE / settings.FPS * dt * settings.TIME_MULTIPLIER
        while self.theta < 0:
            self.theta += 2 * np.pi

    def update(self, dt, sensory_input):
        """
        Updates the bot's internals. "Hunger" can be thought of as a score
        between '-1' and '1' where a greater value means less hungry.
        """
        self.score -= 1.0 / settings.FPS / 10.0 * dt * settings.TIME_MULTIPLIER
        if self.score < -1:
            self.score = -1.0

        no_herbibots = len(list(bot for bot in self.pop.bots if bot.RGB == GREEN))
        no_carnibots = len(list(bot for bot in self.pop.bots if bot.RGB == RED))
        if no_herbibots < 2:
            self.pop.create_herbibots()
        if no_carnibots < 2:
            self.pop.create_carnibots()
        

        if self.pop.time_since_last_death >= 0.2:
            for bot in self.pop.bots:
                if bot.RGB == GREEN and self.RGB == RED and distance_between(self.x, self.y, bot.x, bot.y) <= 2 * Bot.HITBOX_RADIUS :
                    print "Fed bot!"
                    self.pop.feed(self, bot, is_bot = True)
                    break

        self.nnet.feed_forward(sensory_input)
        output = self.nnet.output()
        if seq_is_equal(output, Bot.MOVE_FORWARD):
            self._move_forward(dt)
        elif seq_is_equal(output, Bot.TURN_LEFT):
            self._turn_left(dt)
        elif seq_is_equal(output, Bot.TURN_RIGHT):
            self._turn_right(dt)
        elif seq_is_equal(output, Bot.MOVE_FASTER):
            self._move_faster(dt)


class Food:
    """
    The representation of the red circles.
    """

    # In pixels.
    HITBOX_RADIUS = 5
    RGB = (255, 255, 0)

    def __init__(self, population):
        mid_x = int(settings.WINDOW_WIDTH / 2)
        mid_y = int(settings.WINDOW_HEIGHT / 2)
        max_left_x = mid_x - (Bot.SPAWN_RADIUS + Bot.HITBOX_RADIUS + 5)
        min_right_x = mid_x + (Bot.SPAWN_RADIUS + Bot.HITBOX_RADIUS + 5)
        max_top_y = mid_y - (Bot.SPAWN_RADIUS + Bot.HITBOX_RADIUS + 5)
        min_bottom_y = mid_y + (Bot.SPAWN_RADIUS + Bot.HITBOX_RADIUS + 5)
        self.x = np.random.choice((np.random.uniform(0, max_left_x), np.random.uniform(min_right_x, settings.WINDOW_WIDTH)))
        self.y = np.random.choice((np.random.uniform(0, max_top_y), np.random.uniform(min_bottom_y, settings.WINDOW_HEIGHT)))
        self.pop = population

    def update(self, dt):
        """
        Updates the food's internals and handles bot<->food collision.
        """
        for bot in self.pop.bots:
            if bot.RGB == GREEN and distance_between(self.x, self.y, bot.x, bot.y) <= Bot.HITBOX_RADIUS + Food.HITBOX_RADIUS:
                self.pop.feed(bot, self)
                break

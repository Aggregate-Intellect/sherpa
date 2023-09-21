class BaseAgent:
    def __init__(
        self,
        name: str,
        description: str,
        shared_memory=None,
        belief=None,
        action_selector=None,
        num_runs=1,
    ):
        self.name = name
        self.description = description
        self.shared_memory = shared_memory
        self.belief = belief
        self.action_selector = action_selector
        self.num_runs = num_runs

        self.actions = []
        self.reflections = []
        self.subscribed_events = []

    def add_action(self, action):
        self.actions.append(action)

    def add_reflection(self, reflection):
        self.reflections.append(reflection)

    def run(self):
        finished = False
        runs = 0
        observation = self.observe()

        while not finished and runs < self.num_runs:
            self.belief.update(observation)
            action, inputs = self.action_selector.select_action(self.belief)
            action_output = self.act(action, inputs)
            observation = action_output
            finished = False
            for reflection in self.reflections:
                finished, observation = reflection.reflect(self.belief, observation)
                if finished:
                    break

            runs += 1

        return observation

    def observe(self):
        return self.shared_memory.observe(self.belief)

    def act(self, action, inputs):
        return action.execute(**inputs)

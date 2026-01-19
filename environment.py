import minerl
import gym

env = gym.make('MineRLNavigateDense-v0')

# get observation from agent
obs = env.reset()

# take actions
done = False

while not done:
    # Take a random action
    action = env.action_space.sample()
    # In BASALT environments, sending ESC action will end the episode
    # Lets not do that
    action["ESC"] = 0
    obs, reward, done, _ = env.step(action)
    print(f"reward={reward}") 
    env.render()
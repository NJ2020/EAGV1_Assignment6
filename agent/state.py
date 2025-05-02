# Maintains state of the agent between turns

last_response = None
iteration = 0
iteration_response = []

def reset_state():
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

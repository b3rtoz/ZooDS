import time

def wait_for_responses(stack, timeout, sleep_interval=0.01):
    """
    Waits for responses from the ECU via the provided stack.

    Args:
        stack: Communication interface with methods process(), available(), and recv().
        timeout (float): Time in seconds to wait after the last received frame before stopping.
        sleep_interval (float): Time (in seconds) to sleep between checks.

    Returns:
        List of received response frames.
    """
    responses = []
    last_frame_time = time.time()
    while True:
        stack.process()
        if stack.available():
            response = stack.recv()
            responses.append(response)
            print(f"Received response: {response.hex()}")
            last_frame_time = time.time()  # Reset timeout after each received message
        if time.time() - last_frame_time > timeout:
            break
        time.sleep(sleep_interval)
    return responses

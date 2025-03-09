import can
import time


def send_tester_present_functional(bus, arbitration_id, is_extended_id=False):
    """ Sends Tester Present (UDS service "3E 00") on the given arbitration ID and listens for responses.
    The timeout resets each time a message is received.
    Returns the list of responses (if any)."""
    tester_present_msg = can.Message(
        arbitration_id=arbitration_id,
        data=bytes.fromhex("02 3E 00"),
        is_extended_id=is_extended_id
    )
    try:
        bus.send(tester_present_msg)
        print(f"\nSent Tester Present broadcast: {hex(arbitration_id)}: {tester_present_msg}")
    except can.CanError as e:
        print(f"\nFailed to send Tester Present message on ID {hex(arbitration_id)}: {e}")
        return None

    print("\nListening for Tester Present responses...")
    timeout_gap = 1.0  # seconds: reset timer gap after each received frame
    last_frame_time = time.time()
    responses = []
    while True:
        msg = bus.recv(timeout=0.1)
        if msg:
            responses.append(msg)
            last_frame_time = time.time()  # reset timeout on each frame received
        if time.time() - last_frame_time > timeout_gap:
            break
    if responses:
        for r in responses:
            print(f"\nReceived Tester Present responses:{hex(arbitration_id)}{r}")
    else:
        print(f"\nNo responses received for Tester Present from ID {hex(arbitration_id)}.")
    return responses


def try_functional_broadcast(bus):
    """ Attempts to send a Tester Present functional broadcast using 29-bit, then 11-bit IDs.
    If no responses are received for both, prompts the user to retry or exit."""
    # try 29-bit functional broadcast (standard arbitration ID: 0x18DB33F1)
    responses = send_tester_present_functional(bus, 0x18DB33F1, is_extended_id=True)
    if responses:
        return
    # if no responses to 29-bit broadcast, try 11-bit (standard arbitration ID: 0x7DF)
    responses = send_tester_present_functional(bus, 0x7DF, is_extended_id=False)
    if responses:
        return

    # If still no responses, ask the user to retry, try custom ID, or exit.
    choice = input("No functional broadcast responses from standard arbitration IDs. Try again? (y/n/custom id): ")
    if choice.lower().startswith('y'):
        try_functional_broadcast(bus)
    if choice.lower().startswith('custom'):
        arbitration_id = bytes.fromhex(input("enter arbitration ID to try in hex (e.g., 18DBFFF1, 7FF):"))
        if len(arbitration_id) > 3:
            send_tester_present_functional(bus, arbitration_id, is_extended_id=True)
        if len(arbitration_id) == 3:
            send_tester_present_functional(bus, arbitration_id, is_extended_id=False)
    else:
        bus.shutdown()
        exit(0)


def background_tester_present(bus, arbitration_id, is_extended_id, stop_event):
    """Sends the Tester Present broadcast (02 3E 00) every 1000ms in a background thread."""

    message = can.Message(
        arbitration_id=arbitration_id,
        data=bytes.fromhex("02 3E 00"),
        is_extended_id=is_extended_id
    )
    # send test present on cycle until stop event is detected
    while not stop_event.is_set():
        try:
            bus.send(message)
            print("Background Tester Present sent.")
        except can.CanError as e:
            print(f"Background Tester Present error: {e}")
        # wait 1 sec., look for stop event then loop again
        if stop_event.wait(1.0):
            break

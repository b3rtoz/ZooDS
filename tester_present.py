import can
import time


def send_tester_present_functional(bus, arbitration_id, is_extended_id):
    """
    Send a Tester Present (UDS service '3E 00') message on the given arbitration ID,
    and collect any responses.

    Args:
        bus: The CAN bus instance.
        arbitration_id: The arbitration ID to use for sending.
        is_extended_id: Boolean indicating whether the arbitration ID is extended.

    Returns:
        A list of received CAN messages.
    """
    msg = can.Message(
        arbitration_id=arbitration_id,
        data=bytes.fromhex("02 3E 00"),
        is_extended_id=is_extended_id
    )
    try:
        bus.send(msg)
        print(f"\nSent Tester Present from {hex(arbitration_id)}: {msg}")
    except can.CanError as e:
        print(f"Failed to send Tester Present on {hex(arbitration_id)}: {e}")
        return []

    responses = []
    last_time = time.time()
    timeout_gap = 1.0  # seconds: reset timeout after each received message
    while True:
        r = bus.recv(timeout=0.1)
        if r:
            responses.append(r)
            last_time = time.time()  # Reset timeout on receiving a message
        if time.time() - last_time > timeout_gap:
            break

    if responses:
        for r in responses:
            print(f"Received response from {hex(r.arbitration_id)}: {r}")
    else:
        print(f"No responses for Tester Present on {hex(arbitration_id)}.")
    return responses


def try_functional_broadcast(bus):
    """
    Attempt to send a Tester Present functional broadcast using standard 29-bit and 11-bit IDs.
    If no responses are received, prompt the user to retry, use a custom ID, or exit.

    Returns:
        A unique list of discovered tester IDs extracted from responses.
    """
    discovered_ids = []
    # List of standard arbitration IDs to try: (ID, is_extended_id)
    standard_ids = [
        (0x18DB33F1, True),  # 29-bit standard
        (0x7DF, False)  # 11-bit standard
    ]

    for arb_id, is_ext in standard_ids:
        responses = send_tester_present_functional(bus, arb_id, is_ext)
        discovered_ids.extend(r.arbitration_id for r in responses)

    discovered_ids = list(set(discovered_ids))  # Remove duplicates

    while not discovered_ids:
        choice = input(
            "\nNo responses received. Choose an option:\n"
            "  (y) Try again\n"
            "  (c) Enter custom arbitration ID\n"
            "  (e) Exit\n"
            "Your choice: "
        ).strip().lower()
        if choice.startswith('y'):
            for arb_id, is_ext in standard_ids:
                responses = send_tester_present_functional(bus, arb_id, is_ext)
                discovered_ids.extend(r.arbitration_id for r in responses)
            discovered_ids = list(set(discovered_ids))
        elif choice.startswith('c'):
            custom_id_str = input("Enter custom arbitration ID in hex (e.g., 18DBFFF1 or 7FF): ").strip()
            try:
                custom_id = int(custom_id_str, 16)
            except ValueError:
                print("Invalid hex value. Please try again.")
                continue
            is_ext = custom_id > 0x7FF
            responses = send_tester_present_functional(bus, custom_id, is_ext)
            discovered_ids.extend(r.arbitration_id for r in responses)
            discovered_ids = list(set(discovered_ids))
            if not discovered_ids:
                print("No responses for custom ID.")
        else:
            print("Exiting.")
            bus.shutdown()
            exit(0)

    return discovered_ids


def background_tester_present(bus, arbitration_id, stop_event):
    """
    Continuously send a Tester Present message every 1 second in a background thread,
    until the stop_event is set.

    Args:
        bus: The CAN bus instance.
        arbitration_id: The arbitration ID to use.
        stop_event: A threading.Event that signals when to stop.
    """
    is_ext = arbitration_id > 0x7FF
    msg = can.Message(
        arbitration_id=arbitration_id,
        data=bytes.fromhex("02 3E 00"),
        is_extended_id=is_ext
    )
    while not stop_event.is_set():
        try:
            bus.send(msg)
        except can.CanError as e:
            print(f"Background Tester Present error: {e}")
        if stop_event.wait(1.0):
            break

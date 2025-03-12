import can
import time

def send_tester_present_functional(bus, arbitration_id, is_extended_id):
    """
    Sends a Tester Present (UDS service "3E 00") message on the given arbitration ID
    and collects any responses.

    Args:
        bus: The CAN bus instance.
        arbitration_id (int): The tester arbitration ID to use for sending.
        is_extended_id (bool): True if using 29-bit IDs, False for 11-bit.

    Returns:
        List of received CAN messages.
    """
    tester_present_msg = can.Message(
        arbitration_id=arbitration_id,
        data=bytes.fromhex("02 3E 00"),
        is_extended_id=is_extended_id
    )
    try:
        bus.send(tester_present_msg)
        print(f"\nSent Tester Present from ID {hex(arbitration_id)}: {tester_present_msg}")
    except can.CanError as e:
        print(f"\nFailed to send Tester Present on ID {hex(arbitration_id)}: {e}")
        return []

    print("\nListening for Tester Present responses...")
    timeout_gap = 1.0  # seconds to wait after the last received frame
    last_frame_time = time.time()
    responses = []
    while True:
        msg = bus.recv(timeout=0.1)
        if msg:
            responses.append(msg)
            last_frame_time = time.time()  # Reset timeout on receiving a message
        if time.time() - last_frame_time > timeout_gap:
            break
    if responses:
        for r in responses:
            print(f"Received response from ECU ID {hex(r.arbitration_id)}: {r}")
    else:
        print(f"No responses for Tester Present on ID {hex(arbitration_id)}.")
    return responses

def try_functional_broadcast(bus):
    """
    Attempts to send a Tester Present functional broadcast using standard tester IDs.
    Returns a tuple: (successful_tester_id, [list of ECU arbitration IDs that responded]).

    It first tries a standard 29-bit tester ID (0x18DB33F1) then a standard 11-bit (0x7DF).
    If no responses are received, it prompts the user to retry or enter a custom tester ID.
    The identifier mode (11-bit or 29-bit) is automatically set based on the tester ID value.

    Returns:
        (int, list): A tuple where the first element is the tester arbitration ID used,
                     and the second element is a list of ECU arbitration IDs that responded.
    """
    standard_ids = [
        (0x18DB33F1, True),  # 29-bit tester ID
        (0x7DF, False)       # 11-bit tester ID
    ]
    for tester_id, is_ext in standard_ids:
        responses = send_tester_present_functional(bus, tester_id, is_ext)
        if responses:
            ecu_ids = list({msg.arbitration_id for msg in responses})
            print(f"Functional broadcast successful with tester ID {hex(tester_id)}.")
            print("ECU responses from IDs: " + ", ".join(hex(x) for x in ecu_ids))
            return tester_id, ecu_ids

    # No responses received; prompt the user.
    while True:
        choice = input(
            "\nNo functional broadcast responses from standard tester IDs.\n"
            "Try again? (y), enter custom tester ID? (c), or exit (e): "
        ).strip().lower()
        if choice.startswith('y'):
            for tester_id, is_ext in standard_ids:
                responses = send_tester_present_functional(bus, tester_id, is_ext)
                if responses:
                    ecu_ids = list({msg.arbitration_id for msg in responses})
                    print(f"Functional broadcast successful with tester ID {hex(tester_id)}.")
                    print("ECU responses from IDs: " + ", ".join(hex(x) for x in ecu_ids))
                    return tester_id, ecu_ids
        elif choice.startswith('c'):
            custom_id_str = input("Enter custom tester arbitration ID in hex (e.g., 18DBFFF1 or 7DF): ").strip()
            try:
                custom_id = int(custom_id_str, 16)
            except ValueError:
                print("Invalid hex value. Please try again.")
                continue
            is_ext = custom_id > 0x7FF  # Automatically determine ID length.
            responses = send_tester_present_functional(bus, custom_id, is_ext)
            if responses:
                ecu_ids = list({msg.arbitration_id for msg in responses})
                print(f"Functional broadcast successful with tester ID {hex(custom_id)}.")
                print("ECU responses from IDs: " + ", ".join(hex(x) for x in ecu_ids))
                return custom_id, ecu_ids
            else:
                print("No responses for custom tester ID.")
        else:
            bus.shutdown()
            exit(0)

def background_tester_present(bus, arbitration_id, stop_event):
    """
    Continuously sends a Tester Present message every 1 second in a background thread,
    until the stop_event is set.

    Args:
        bus: The CAN bus instance.
        arbitration_id (int): The tester arbitration ID to use.
        stop_event: A threading.Event that signals when to stop.
    """
    is_ext = arbitration_id > 0x7FF
    message = can.Message(
        arbitration_id=arbitration_id,
        data=bytes.fromhex("02 3E 00"),
        is_extended_id=is_ext
    )
    while not stop_event.is_set():
        try:
            bus.send(message)
        except can.CanError as e:
            print(f"Background Tester Present error: {e}")
        if stop_event.wait(1.0):
            break

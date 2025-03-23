from zooDS import did_scan, mem_scan, tester_present, utils, rid_scan, key_crack
from zooDS.utils import set_can_channel, stack_parms, set_isotp_stack, get_hex_input


def zds():
    # Set up the CAN interface.
    bus = set_can_channel(input("Enter CAN interface (e.g., can0, vcan0): ").strip())

    # Option to discover valid tester arbitration ID.
    if input("Attempt to discover valid tester ID? (y/n): ").strip().lower().startswith('y'):
        tester_id = utils.process_id_result(tester_present.try_functional_broadcast(bus))
    else:
        tester_id = get_hex_input("Enter tester (source) id in hex: ")

    # Create the ISO-TP stack
    stack = set_isotp_stack(stack_parms(bus, tester_id))

    # User command loop.
    while True:
        user_choice = input(
            "\nChoose an option or enter a UDS service in hex:\n"
            "1. Scan DIDs\n"
            "2. Scan RIDs\n"
            "3. Scan Memory by Address\n"
            "4. Update Tester/ECU IDs"
            "5. Exit\n"
            "Or enter a UDS service (e.g., 10 01): "
        ).strip()

        if user_choice == "1":
            did_scan.try_all_dids(stack)
            continue
        elif user_choice == "2":
            rid_scan.try_all_rids(stack)
            continue
        elif user_choice == "3":
            mem_scan.try_memory_scan(stack)
            continue
        elif user_choice == "4":
            tester_id = utils.get_hex_input("Enter Tester (source) id in hex: ")
            stack = set_isotp_stack(stack_parms(bus, tester_id))
            continue
        elif user_choice == "5":
            bus.shutdown()
            print("Shutting down CAN bus.")
            break

        # if no. 1-5 is not entered, treat the input as a custom UDS service in hex.
        try:
            service_bytes = bytes.fromhex(user_choice)
        except ValueError:
            print("Invalid hex input. Please try again.")
            continue

        print(f"Sending UDS service: {user_choice}...")
        stack.send(service_bytes)
        responses = utils.wait_for_responses(stack, timeout=0.3)

        if responses:
            for resp in responses:
                utils.print_response(resp, service_bytes)
        else:
            print("No UDS response received within timeout.")

        # If Security Access (0x27) is requested, delegate handling to key_crack.
        if service_bytes[0] == 0x27 and responses:
            key_crack.handle_security_access(service_bytes, responses, stack)

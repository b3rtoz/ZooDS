import can
import did_scan
import rid_scan
import tester_present
import key_crack
import zoo_utils


def main():
    # Set up the CAN interface.
    interface = input("Enter CAN interface (e.g., can0, vcan0): ").strip()
    try:
        bus = can.interface.Bus(channel=interface, interface='socketcan', timeout=0.3)
    except Exception as e:
        print(f"Error opening interface {interface}: {e}")
        return

    # Option to discover valid tester arbitration ID.
    if input("Attempt to discover valid tester ID? (y/n): ").strip().lower().startswith('y'):
        result = tester_present.try_functional_broadcast(bus)
        if result and isinstance(result, tuple):
            discovered_tester, ecu_ids = result
            print(f"Discovered tester ID: {hex(discovered_tester)}")
            print("ECU responses from: " + ", ".join(hex(each_id) for each_id in ecu_ids))
            choice = input("Use discovered tester ID? (y/n): ").strip().lower()
            if choice.startswith('y'):
                tester_id = discovered_tester
            else:
                tester_id = zoo_utils.get_hex_input("Enter Tester (source) id in hex: ")
        else:
            tester_id = zoo_utils.get_hex_input("Enter Tester (source) id in hex: ")
    else:
        tester_id = zoo_utils.get_hex_input("Enter Tester (source) id in hex: ")

    ecu_id = zoo_utils.get_hex_input("Enter target ECU (destination) id in hex: ")
    if tester_id is None or ecu_id is None:
        return

    # Automatically determine the identifier mode based on the tester ID.
    if tester_id > 0x7FF:
        id_mode = "29"
    else:
        id_mode = "11"
        print(f"Automatically setting arbitration ID length to {id_mode}-bit based on Tester ID {hex(tester_id)}.")

    # Create the ISO-TP stack using the centralized utility.
    stack = zoo_utils.create_iso_tp_stack(bus, tester_id, ecu_id, id_mode=id_mode)
    print(f"ISO-TP stack created with Tester ID {hex(tester_id)} and ECU ID {hex(ecu_id)} using {id_mode}-bit identifiers.")

    # Main loop to process UDS commands.
    while True:
        user_choice = input(
            "\nChoose an option or enter a UDS service in hex:\n"
            "1. Scan DIDs\n"
            "2. Scan RIDs\n"
            "3. Scan Memory by Address\n"
            "4. Exit\n"
            "Or enter a UDS service (e.g., 10 01): "
        ).strip()

        if user_choice == "1":
            did_scan.try_all_dids(stack)
            continue
        elif user_choice == "2":
            rid_scan.try_all_rids(stack)
            continue
        elif user_choice == "3":
            import mem_scan
            mem_scan.try_memory_scan(stack)
            continue
        elif user_choice == "4":
            bus.shutdown()
            print("Shutting down CAN bus.")
            break

        # Otherwise, treat the input as a custom UDS service in hex.
        try:
            service_bytes = bytes.fromhex(user_choice)
        except ValueError:
            print("Invalid hex input. Please try again.")
            continue

        print(f"Sending UDS service: {user_choice}...")
        stack.send(service_bytes)
        responses = zoo_utils.wait_for_responses(stack, timeout=0.3)

        if responses:
            for resp in responses:
                zoo_utils.print_response(resp, service_bytes)
        else:
            print("No UDS response received within timeout.")

        # If Security Access (0x27) is requested, delegate handling to key_crack.
        if service_bytes[0] == 0x27 and responses:
            key_crack.handle_security_access(service_bytes, responses, stack)

if __name__ == '__main__':
    main()

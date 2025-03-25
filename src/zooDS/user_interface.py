"""
zooDS main module that provides an interactive command-line interface for UDS (Unified Diagnostic Services) 
communications over CAN bus. This module allows scanning DIDs, RIDs, memory addresses, 
and sending custom UDS services.
"""
from zooDS import did_scan, mem_scan, tester_present, utils, rid_scan, key_crack
from .utils import set_can_channel, stack_parms, set_isotp_stack, get_hex_input


def zds():
    """
    Main function that provides a CLI for UDS communications.
    Handles CAN interface setup, UDS commands.
    """

    bus = None
    try:
        # Set up the CAN interface with error handling
        interface = input("Enter CAN interface (e.g., can0, vcan0): ").strip()
        try:
            bus = set_can_channel(interface)
            if not bus:
                print(f"Failed to initialize CAN interface '{interface}'. Exiting.")
                return
        except Exception as e:
            print(f"Error setting up CAN interface: {e}")
            return

        # Option to discover valid tester arbitration ID.
        if input("Attempt to discover valid tester ID? (y/n): ").strip().lower().startswith('y'):
            try:
                tester_id = utils.process_id_result(tester_present.try_functional_broadcast(bus))
                if not tester_id:
                    print("Failed to discover a valid tester ID.")
                    tester_id = get_hex_input("Enter tester (source) id in hex: ")
            except Exception as e:
                print(f"Error during tester ID discovery: {e}")
                tester_id = get_hex_input("Enter tester (source) id in hex: ")
        else:
            tester_id = get_hex_input("Enter tester (source) id in hex: ")

        # Create the ISO-TP stack with proper parameters
        try:
            parms = stack_parms(bus, tester_id)
            stack = set_isotp_stack(parms)
        except Exception as e:
            print(f"Error setting up ISO-TP stack: {e}")
            return

        # Set default timeout for responses, allow configuration
        default_timeout = 0.3
        timeout = input(f"Enter response timeout in seconds (default: {default_timeout}): ").strip()
        if timeout:
            try:
                default_timeout = float(timeout)
                print(f"Timeout set to {default_timeout} seconds")
            except ValueError:
                print(f"Invalid timeout value. Using default: {default_timeout} seconds")

        # User command loop.
        while True:
            user_choice = input(
                "\nChoose an option or enter a UDS service in hex:\n"
                "1. Scan DIDs\n"
                "2. Scan RIDs\n"
                "3. Scan Memory by Address\n"
                "4. Update Tester/ECU IDs\n"
                "5. Configure Timeout\n"
                "6. Exit\n"
                "Or enter a UDS service (e.g., 10 01): "
            ).strip()

            if user_choice == '1':
                    did_scan.try_all_dids(stack, timeout=default_timeout)
            elif user_choice == '2':
                    rid_scan.try_all_rids(stack, timeout=default_timeout)
            elif user_choice == '3':
                    mem_scan.try_memory_scan(stack, timeout=default_timeout)
            elif user_choice == '4':
                # Update both tester and ECU IDs
                tester_id = get_hex_input("Enter Tester (source) id in hex: ")
                try:
                    stack_params = stack_parms(bus, tester_id)
                    stack = set_isotp_stack(stack_params)
                    print("IDs updated successfully")
                except Exception as e:
                    print(f"Error updating IDs: {e}")
            elif user_choice == '5':
                # Allow timeout configuration
                try:
                    new_timeout = float(input("Enter new timeout value in seconds: ").strip())
                    default_timeout = new_timeout
                    print(f"Timeout updated to {default_timeout} seconds")
                except ValueError:
                    print("Invalid timeout value. Keeping current setting.")
            elif user_choice == '6':
                    break
            else:
                try:
                    service_bytes = bytes.fromhex(user_choice)
                except ValueError:
                    print("Invalid hex input. Please try again.")
                    continue

                print(f"Sending UDS service: {user_choice}...")
                stack.send(service_bytes)
                responses = utils.wait_for_responses(stack, timeout=default_timeout)

                if responses:
                    for resp in responses:
                        utils.print_response(resp, service_bytes)
                else:
                    print("No UDS response received within timeout.")

                # If Security Access (0x27) is requested, delegate handling to key_crack.
                if service_bytes[0] == 0x27 and responses:
                    key_crack.handle_security_access(service_bytes, responses, stack)

    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # shut down bus
        if bus:
            try:
                bus.shutdown()
                print("CAN bus shutdown complete.")
            except Exception as e:
                print(f"Error during bus shutdown: {e}")
# fileOperation/checkFiles.py
# import ast  # REMOVE this import, it's no longer needed if saving raw string
import os

def check(file_location_1, file_location_2, variable):
    """
    Compares a specific 'variable' value from two files,
    assuming the files contain raw multi-line QR code data
    with 'key: value' pairs.
    """
    try:
        with open(file_location_1, 'r') as file1:
            content_1 = file1.read() # Read directly, no ast.literal_eval

        with open(file_location_2, 'r') as file2:
            content_2 = file2.read() # Read directly, no ast.literal_eval

        result_1 = {}
        result_2 = {}

        # Parse content_1
        for line in content_1.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                result_1[key.strip()] = value.strip()

        # Parse content_2
        for line in content_2.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                result_2[key.strip()] = value.strip()

        variable = variable.strip()

        value_1 = result_1.get(variable)
        value_2 = result_2.get(variable)

        if value_1 is not None and value_2 is not None and value_1 == value_2:
            print(f"Comparison: '{variable}' value in file 1: '{value_1}'")
            print(f"Comparison: '{variable}' value in file 2: '{value_2}'")
            return True
        else:
            print(f"Comparison: '{variable}' value in file 1: '{value_1}'")
            print(f"Comparison: '{variable}' value in file 2: '{value_2}'")
            return False

    except FileNotFoundError:
        print(f"Error: One of the files not found. File1: {file_location_1}, File2: {file_location_2}")
        return False
    except Exception as e: # Catch any other errors
        print(f"An unexpected error occurred in comparison module: {e}")
        return False

if __name__ == '__main__':
    # This block is for testing the comparison module independently
    # Create dummy files for testing in the *raw multi-line string* format
    dummy_dir = os.path.dirname(os.path.abspath(__file__))
    dummy_file_1_path = os.path.join(dummy_dir, "test_qr_1.txt")
    dummy_file_2_path = os.path.join(dummy_dir, "test_qr_2.txt")
    dummy_file_3_path = os.path.join(dummy_dir, "test_qr_3.txt")

    # Example QR data in the raw multi-line string format
    qr_data_1 = "Name: John Doe\nRoll: 22001011001\nDegree: BE"
    qr_data_2 = "Name: Jane Smith\nRoll: 22001011001\nDegree: BE" # Same Roll
    qr_data_3 = "Name: Peter Jones\nRoll: 22001011002\nDegree: MBA" # Different Roll

    with open(dummy_file_1_path, 'w') as f:
        f.write(qr_data_1)
    with open(dummy_file_2_path, 'w') as f:
        f.write(qr_data_2)
    with open(dummy_file_3_path, 'w') as f:
        f.write(qr_data_3)

    print("\n--- Testing fileOperations/checkFiles.py directly ---")
    to_check = "Degree" # Testing with Degree now

    print(f"\nTest 1: Comparing test_qr_1.txt and test_qr_2.txt for '{to_check}'")
    var = check(
        dummy_file_1_path,
        dummy_file_2_path,
        to_check
    )
    if var:
        print(f"Result: Success ({to_check} matches)")
    else:
        print(f"Result: Failure ({to_check} does not match or error)")

    print(f"\nTest 2: Comparing test_qr_1.txt and test_qr_3.txt for '{to_check}'")
    var = check(
        dummy_file_1_path,
        dummy_file_3_path,
        to_check
    )
    if var:
        print(f"Result: Success ({to_check} matches)")
    else:
        print(f"Result: Failure ({to_check} does not match or error)")

    # Clean up dummy files
    os.remove(dummy_file_1_path)
    os.remove(dummy_file_2_path)
    os.remove(dummy_file_3_path)
    print("\nDummy test files cleaned up.")
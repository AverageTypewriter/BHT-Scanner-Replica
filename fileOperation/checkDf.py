# fileOperation/checkDf.py
import pandas as pd
import os 

def compare(file_path_1, file_path_2, start_a, end_a, start_b, end_b):
    """
    Compares CustomerID from CSV (looked up using product ID from file_path_1)
    with sliced CustomerID from QR2 (from file_path_2).

    Args:
        file_path_1 (str): Path to the temporary file containing the ProductID
                           that was found *within* QR1 content and exists in the CSV.
        file_path_2 (str): Path to the temporary file containing the raw QR2 content.
        start_a (int): Start index for slicing CSV CustomerID.
        end_a (int): End index for slicing CSV CustomerID.
        start_b (int): Start index for slicing QR2 CustomerID.
        end_b (int): End index for slicing QR2 CustomerID.

    Returns:
        bool: True if the sliced main parts of Customer IDs match, False otherwise.
    """
    print("\n--- DEBUG: Entering cmp.compare function (Main Part Only) ---")

    # Read the ProductID (already looked up from CSV) from the first temporary file
    product_id_from_file1 = ""
    try:
        with open(file_path_1, 'r') as f1:
            product_id_from_file1 = f1.read().strip()
        print(f"DEBUG: Read ProductID for lookup from {file_path_1}: '{product_id_from_file1}' (length: {len(product_id_from_file1)})")
    except FileNotFoundError:
        print(f"ERROR: File not found: {file_path_1}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to read {file_path_1}: {e}")
        return False

    # Read raw customer ID from the second temporary file (from QR2 scan)
    customer_id_from_qr2 = ""
    try:
        with open(file_path_2, 'r') as f2:
            customer_id_from_qr2 = f2.read().strip()
        print(f"DEBUG: Read raw Customer ID from QR2 file {file_path_2}: '{customer_id_from_qr2}' (length: {len(customer_id_from_qr2)})")
    except FileNotFoundError:
        print(f"ERROR: File not found: {file_path_2}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to read {file_path_2}: {e}")
        return False

    # Load the CSV file
    csv_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'userr.csv')
    df_internal = pd.DataFrame() 
    try:
        df_internal = pd.read_csv(csv_file_path, encoding='utf-8-sig', engine='python', sep=',', on_bad_lines='skip')
        df_internal.columns = df_internal.columns.str.strip().str.lower()
        if 'productid' not in df_internal.columns or 'customerid' not in df_internal.columns:
            print(f"ERROR: CSV column error: 'productid' or 'customerid' not found in {csv_file_path}")
            print(f"DEBUG: CSV columns found: {df_internal.columns.tolist()}")
            return False
        df_internal['productid'] = df_internal['productid'].astype(str).str.strip()
        df_internal['customerid'] = df_internal['customerid'].astype(str).str.strip()
        print(f"DEBUG: Successfully loaded CSV: {csv_file_path}")
    except FileNotFoundError:
        print(f"ERROR: CSV file not found at {csv_file_path}")
        return False
    except Exception as e:
        print(f"ERROR: Error loading CSV in cmp.compare: {e}")
        return False

    # Use the product_id_from_file1 (which is the matched CSV ProductID) to find the CustomerID in the DataFrame
    matching_rows = df_internal.loc[df_internal['productid'] == product_id_from_file1]

    if matching_rows.empty:
        print(f"DEBUG: No matching ProductID '{product_id_from_file1}' found in CSV for direct lookup.")
        # This case should ideally not be hit if scan_and_compare_qrcodes correctly populated file_path_1
        return False
    else:
        csv_customer_id = str(matching_rows['customerid'].iloc[0]).strip()
        print(f"DEBUG: Found matching ProductID. CSV Customer ID for comparison: '{csv_customer_id}' (length: {len(csv_customer_id)})")

    # Perform string slicing for the main part
    csv_main_part = ""
    qr2_main_part = ""
    try:
        csv_main_part = csv_customer_id[start_a:end_a].strip()
        qr2_main_part = customer_id_from_qr2[start_b:end_b].strip()
        print(f"DEBUG: Slicing Parameters (Main): CSV[{start_a}:{end_a}], QR2[{start_b}:{end_b}]")
        print(f"DEBUG: CSV Main Part (sliced): '{csv_main_part}' (length: {len(csv_main_part)})")
        print(f"DEBUG: QR2 Main Part (sliced): '{qr2_main_part}' (length: {len(qr2_main_part)})")
    except IndexError as e:
        print(f"ERROR: Indexing error for main part slicing. Check your start/end parameters. Error: {e}")
        print(f"DEBUG: CSV Customer ID before slice: '{csv_customer_id}'")
        print(f"DEBUG: QR2 Customer ID before slice: '{customer_id_from_qr2}'")
        return False

    final_match = (csv_main_part == qr2_main_part)
    print(f"DEBUG: Main Parts Match Result: {final_match} ('{csv_main_part}' == '{qr2_main_part}')")
    print("--- DEBUG: Exiting cmp.compare function ---")
    return final_match
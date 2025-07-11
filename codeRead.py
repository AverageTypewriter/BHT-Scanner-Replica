import cv2
from pyzbar.pyzbar import decode
from PIL import Image
import os
import time
import numpy as np
import pandas as pd
from fileOperation import checkDf as cmp
import tkinter as tk
from tkinter import simpledialog, messagebox
import re

# --- GUI Helper Function ---

def get_integer_input_gui(prompt, title):
    root = tk.Tk()
    root.withdraw()
    while True:
        try:
            value = simpledialog.askinteger(title, prompt)
            if value is None:
                messagebox.showinfo("Cancelled", "Input cancelled. Exiting application.")
                return None
            return value
        except ValueError:
            messagebox.showerror("Invalid Input", "Invalid input. Please enter an integer.")
        finally:
            # Ensure the Tkinter window is properly destroyed, especially important in loops
            try:
                root.destroy()
            except:
                pass

# --- Helper function to extract quantity from QR data ---

def extract_quantity(qr_data):
    """Extracts the last 4 characters of the QR code data as the quantity."""
    if qr_data is None:
        return ""
    # Ensure the data is treated as a string and handle potential encoding issues if needed
    data_str = str(qr_data).strip()
    
    # We assume the quantity is strictly the last 4 characters
    if len(data_str) >= 4:
        return data_str[-4:]
    else:
        # If the string is shorter than 4 characters, return the whole string or handle as needed
        return data_str

# --- Main QR Scanning and Comparison Function ---

def scan_and_compare_qrcodes():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = script_dir
    
    # Define file paths for temporary storage and output
    # This file stores the matched ProductID from CSV, which is needed for the cmp.compare lookup
    qr1_content_for_cmp_file = os.path.join(output_dir, "qr_1_content_for_cmp.txt") 
    qr2_content_file = os.path.join(output_dir, "qr_2_content.txt") # Stores raw QR2 content
    csv_file_path = os.path.join(output_dir, 'userr.csv')
    
    # New output file for logging successful matches
    match_log_file = os.path.join(output_dir, "match_log.txt")

    print(f"DEBUG: Script directory: {script_dir}")
    print(f"DEBUG: Expected csv_file_path: {csv_file_path}")
    print(f"DEBUG: Expected match_log_file path: {match_log_file}")

    # Initial cleanup of temporary files
    for f in [qr1_content_for_cmp_file, qr2_content_file]:
        if os.path.exists(f):
            print(f"DEBUG: Removing existing temporary file: {f}")
            os.remove(f)
    
    # Load and preprocess CSV data
    try:
        df = pd.read_csv(csv_file_path, encoding='utf-8-sig', engine='python', sep=',', on_bad_lines='skip')
        
        df.columns = df.columns.str.strip().str.lower()

        if 'productid' not in df.columns or 'customerid' not in df.columns:
            messagebox.showerror("CSV Column Error", f"Error: 'productid' or 'customerid' column not found in the CSV file.\nAvailable columns: {df.columns.tolist()}")
            return
        
        df['productid'] = df['productid'].astype(str).str.strip() 
        df['customerid'] = df['customerid'].astype(str).str.strip() 

    except FileNotFoundError:
        messagebox.showerror("CSV Error", f"Error: CSV file '{csv_file_path}' not found.")
        return
    except Exception as e:
        messagebox.showerror("CSV Error", f"Error reading CSV file '{csv_file_path}': {e}")
        return

    # Get slicing parameters from the user via GUI
    messagebox.showinfo("Input Parameters", 
                         "Please enter the string slicing parameters for the main part.\n\n"
                         "These define which parts of the CustomerID strings will be compared.")

    start_a = get_integer_input_gui("Enter start index for CSV CustomerID (main part): ", "CSV Main Start")
    if start_a is None: return
    end_a = get_integer_input_gui("Enter end index for CSV CustomerID (main part): ", "CSV Main End")
    if end_a is None: return
    start_b = get_integer_input_gui("Enter start index for QR2 CustomerID (main part): ", "QR2 Main Start")
    if start_b is None: return
    end_b = get_integer_input_gui("Enter end index for QR2 CustomerID (main part): ", "QR2 Main End")
    if end_b is None: return
    
    messagebox.showinfo("Parameters Set", "Parameters set. Initializing camera...")

    # Initialize camera
    cap = None
    for i in range(0, 3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Camera opened at index {i}")
            break
        if cap: cap.release() 
    
    if not cap or not cap.isOpened():
        messagebox.showerror("Camera Error", "Error: Could not open any webcam.")
        print("Error: Could not open any webcam.")
        return

    # Define workflow states
    SCAN_PRODUCT = 0
    SCAN_CUSTOMER = 1
    COMPARE_RESULT = 2
    current_state = SCAN_PRODUCT

    # Variables for state tracking and display (colors and fonts)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    font_thickness = 1
    line_type = cv2.LINE_AA
    text_color = (255, 255, 255)
    highlight_color = (0, 255, 0)
    warning_color = (0, 0, 255)
    info_color = (0, 255, 255)
    
    y_start = 30
    y_offset = 30

    current_data = None 
    comparison_result = False
    
    # Variables to store data across states
    scanned_qr1_raw_content = "" # Raw content of the first QR code scanned
    qr1_product_id = "" # The ProductID found as substring in QR1, from CSV
    qr1_qty = "" # Quantity from QR1
    csv_customer_id = "" # The CustomerID associated with the ProductID from CSV
    qr2_raw_content = "" # Raw content of the second QR code scanned
    qr2_qty = "" # Quantity from QR2

    print("\n=== QR Code Scanner Workflow Started ===")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
        
        # Decode QR codes
        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        decoded_objects = decode(pil_img)
        
        current_data = None 
        if decoded_objects:
            obj = decoded_objects[0]
            current_data = obj.data.decode('utf-8').strip()
            
            # Draw polygon around detected QR code
            points = obj.polygon
            if len(points) == 4:
                pts = [(p.x, p.y) for p in points]
                pts = np.array(pts, np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], True, (0, 255, 0), 2)

        # --- Display UI and Workflow Status ---
        y_pos = y_start
        
        if current_state == SCAN_PRODUCT:
            status_text = "STATE: Scan PRODUCT QR"
            action_text = "Press 's' to SAVE product QR & Lookup CSV"
            status_color = info_color
            # Displaying previously scanned data for context
            if qr1_product_id:
                cv2.putText(frame, f"Product ID (CSV): {qr1_product_id}", (20, y_pos + y_offset*2), font, font_scale * 0.7, (255, 255, 0), font_thickness, line_type)
                cv2.putText(frame, f"CSV Customer ID: {csv_customer_id}", (20, y_pos + y_offset*3), font, font_scale * 0.7, (255, 255, 0), font_thickness, line_type)
                cv2.putText(frame, f"QR1 Qty: {qr1_qty}", (20, y_pos + y_offset*4), font, font_scale * 0.7, (255, 255, 0), font_thickness, line_type)

        elif current_state == SCAN_CUSTOMER:
            status_text = "STATE: Scan CUSTOMER QR"
            action_text = "Press 's' to SAVE customer QR & COMPARE"
            status_color = info_color
            if qr1_product_id:
                cv2.putText(frame, f"Product ID (CSV): {qr1_product_id}", (20, y_pos + y_offset*2), font, font_scale * 0.7, (255, 255, 0), font_thickness, line_type)
                cv2.putText(frame, f"CSV Customer ID: {csv_customer_id}", (20, y_pos + y_offset*3), font, font_scale * 0.7, (255, 255, 0), font_thickness, line_type)
                cv2.putText(frame, f"QR1 Qty: {qr1_qty}", (20, y_pos + y_offset*4), font, font_scale * 0.7, (255, 255, 0), font_thickness, line_type)
        
        else: # COMPARE_RESULT
            if comparison_result:
                status_text = "RESULT: MATCH FOUND! (Press 's' for new scan)"
                action_text = "Press 's' to start NEW product scan"
                status_color = highlight_color
            else:
                status_text = "RESULT: NO MATCH! (Press 's' to rescan customer)"
                action_text = "Press 's' to RESCAN customer QR"
                status_color = warning_color
            
            cv2.putText(frame, f"Product ID (CSV): {qr1_product_id}", (20, y_pos + y_offset*2), font, font_scale * 0.7, (255, 255, 0), font_thickness, line_type)
            cv2.putText(frame, f"CSV Customer ID: {csv_customer_id}", (20, y_pos + y_offset*3), font, font_scale * 0.7, (255, 255, 0), font_thickness, line_type)
            cv2.putText(frame, f"QR1 Qty: {qr1_qty}", (20, y_pos + y_offset*4), font, font_scale * 0.7, (255, 255, 0), font_thickness, line_type)
            cv2.putText(frame, f"QR2 Qty: {qr2_qty}", (20, y_pos + y_offset*5), font, font_scale * 0.7, (255, 255, 0), font_thickness, line_type)


        # Display status and action text
        for i, line in enumerate([status_text, action_text]):
            text_size = cv2.getTextSize(line, font, font_scale, font_thickness)[0]
            cv2.rectangle(frame, (10, y_pos - text_size[1] - 5), (10 + text_size[0] + 10, y_pos + 5), (0, 0, 0), -1)
            cv2.putText(frame, line, (20, y_pos), font, font_scale, 
                                     status_color if i == 0 else text_color, 
                                     font_thickness, line_type)
            y_pos += y_offset

        # Display detected QR data
        if current_data:
            data_lines = [current_data[i:i+40] for i in range(0, len(current_data), 40)]
            cv2.putText(frame, "Detected QR Data:", (20, y_pos), font, font_scale * 0.8, (255, 255, 0), font_thickness, line_type)
            y_pos += 25
            for line in data_lines:
                text_size = cv2.getTextSize(line, font, font_scale*0.8, font_thickness)[0]
                cv2.rectangle(frame, (10, y_pos - text_size[1] - 5), (10 + text_size[0] + 10, y_pos + 5), (0, 0, 0), -1)
                cv2.putText(frame, line, (20, y_pos), font, font_scale*0.8, 
                                     (255,255,0), font_thickness, line_type)
                y_pos += 25

        cv2.putText(frame, "Press 'q' to quit", (10, frame.shape[0]-20), 
                             font, 0.6, (255,255,255), 1, line_type)

        cv2.imshow("QR Code Scanner", frame)

        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        
        elif key == ord('s'):
            if not current_data:
                print("No QR code detected to save.")
                continue
                
            if current_state == SCAN_PRODUCT:
                scanned_qr1_raw_content = current_data
                qr1_qty = extract_quantity(current_data)
                
                found_match = False
                temp_product_id = ""
                temp_customer_id = ""

                # Find ProductID match in CSV as a substring of the scanned QR1 data
                for index, row in df.iterrows():
                    csv_product_id = row['productid']
                    if csv_product_id in scanned_qr1_raw_content:
                        temp_product_id = csv_product_id
                        temp_customer_id = str(row['customerid']).strip()
                        found_match = True
                        break 
                
                if not found_match:
                    messagebox.showwarning("Product ID Not Found", 
                                           f"No ProductID from '{csv_file_path}' found in QR1 content.")
                    print(f"No ProductID from '{csv_file_path}' found in QR1 content: '{scanned_qr1_raw_content}'")
                    qr1_product_id = "" 
                    csv_customer_id = ""
                    qr1_qty = ""
                    continue 
                else:
                    # Store the matched Product ID and Customer ID from CSV
                    qr1_product_id = temp_product_id
                    csv_customer_id = temp_customer_id
                    print(f"Scanned Product QR (Raw): '{scanned_qr1_raw_content}'")
                    print(f"Found matching ProductID from CSV: '{qr1_product_id}'")
                    print(f"Extracted CSV CustomerID: '{csv_customer_id}'")
                    print(f"Extracted QR1 Quantity: '{qr1_qty}'")

                    try:
                        # Write the matched CSV ProductID to the temporary file. 
                        # This is used by cmp.compare to ensure the CustomerID in QR2 belongs to a valid ProductID.
                        with open(qr1_content_for_cmp_file, 'w') as f:
                            f.write(qr1_product_id) 
                        print(f"Saved matched CSV ProductID to '{qr1_content_for_cmp_file}'")
                        current_state = SCAN_CUSTOMER 
                    except Exception as e:
                        print(f"ERROR: Failed to write to {qr1_content_for_cmp_file}: {e}")
                        messagebox.showerror("File Write Error", f"Error saving matched ProductID: {e}")
            
            elif current_state == SCAN_CUSTOMER:
                qr2_raw_content = current_data
                qr2_qty = extract_quantity(current_data)
                
                try:
                    # Write the raw QR2 content to the temporary file
                    with open(qr2_content_file, 'w') as f:
                        f.write(qr2_raw_content)
                    print(f"Saved QR2 content to '{qr2_content_file}'")
                    print(f"Extracted QR2 Quantity: '{qr2_qty}'")
                    
                    # Perform comparison using the file paths
                    comparison_result = cmp.compare(
                        qr1_content_for_cmp_file, qr2_content_file, 
                        start_a, end_a, start_b, end_b
                    )
                    
                    print(f"Comparison result: {'MATCH' if comparison_result else 'NO MATCH'}")
                    
                    if comparison_result:
                        messagebox.showinfo("Comparison Result", "MATCH FOUND!")
                        # Log the successful match
                        # Change made here: Use 'scanned_qr1_raw_content' instead of 'qr1_product_id' 
                        # for the QR1 field in the log file, as requested.
                        log_entry = f"{scanned_qr1_raw_content}\t{qr2_raw_content}\t{qr1_qty}\t{qr2_qty}\n"
                        try:
                            with open(match_log_file, 'a') as log_f:
                                log_f.write(log_entry)
                            print(f"Successfully logged match to '{match_log_file}'")
                        except Exception as log_e:
                            print(f"ERROR: Failed to log match to file: {log_e}")
                            messagebox.showerror("Log Error", f"Failed to log match to file: {log_e}")
                    else:
                        messagebox.showwarning("Comparison Result", "NO MATCH!")

                    current_state = COMPARE_RESULT
                
                except Exception as e:
                    print(f"ERROR: Error during QR2 save or comparison: {e}")
                    messagebox.showerror("Error", f"An error occurred during comparison: {e}")
                    
            elif current_state == COMPARE_RESULT:
                if comparison_result:
                    # If match found, reset for a new product scan
                    print("DEBUG: Match found, resetting for new scan. Removing content files.")
                    for f in [qr1_content_for_cmp_file, qr2_content_file]:
                        if os.path.exists(f):
                            os.remove(f)
                    
                    # Reset state variables for next scan cycle
                    scanned_qr1_raw_content = ""
                    qr1_product_id = "" 
                    qr1_qty = ""
                    csv_customer_id = ""
                    qr2_raw_content = ""
                    qr2_qty = ""
                    current_state = SCAN_PRODUCT
                    print("Ready for new product scan.")
                else:
                    # If no match, allow rescan of the customer QR
                    print("DEBUG: No match, allowing rescan of customer QR. Removing qr2_content_file.")
                    if os.path.exists(qr2_content_file):
                        os.remove(qr2_content_file)
                    qr2_raw_content = ""
                    qr2_qty = ""
                    current_state = SCAN_CUSTOMER
                    print("Please rescan customer QR.")

    # Cleanup upon exit
    cap.release()
    cv2.destroyAllWindows()
    print("DEBUG: Application closed. Final cleanup of temporary content files.")
    for f in [qr1_content_for_cmp_file, qr2_content_file]:
        if os.path.exists(f):
            os.remove(f)

if __name__ == "__main__":
    scan_and_compare_qrcodes()


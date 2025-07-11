import qrcode
import os

def create_qr_code_from_file(file_path):
    # ... (previous code for create_qr_code_from_file function) ...
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()

        if not file_content.strip():
            print(f"Warning: File '{file_path}' is empty or contains only whitespace. QR code will be empty.")
            qr_data = ""
        else:
            qr_data = file_content

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )

        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        file_name_without_ext = os.path.splitext(os.path.basename(file_path))[0]
        output_qr_filename = f"{file_name_without_ext}_qrcode.png"

        output_qr_path = os.path.join(os.path.dirname(os.path.abspath(file_path)), output_qr_filename)

        img.save(output_qr_path)
        print(f"QR Code successfully generated and saved to: {output_qr_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # --- Example Usage ---
    # 1. Create a dummy text file for testing

    # No 'with open' block here if you don't want to create the file
    # If dummyFile1.txt doesn't exist, create_qr_code_from_file will report an error.

    # Now, let's create a QR code from its content

    for num in range(1,3):
        dummy_file_name = f"dummy_file_{num}.txt"
        print(f"\n--- Generating QR Code from 'dummyFile{num}.txt' ---")
        create_qr_code_from_file(dummy_file_name)


    # with open(f'dummy_file_2.txt', 'w') as file:
    #     file.write(f'HHID3004ID0018')

    print("\nGeneration process complete.")
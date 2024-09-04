import subprocess
import os
import glob

# This script is designed to compile and upload Arduino code to a coprocessor
# on a LattePanda Delta 3 board. The coprocessor is connected via an internal USB bus,
# which might be confusing to users at first, as it's not an external connection.
# This script uses the arduino-cli tool and shows how these can be used to avoid having to 
# manually compile and upload Arduino code to the coprocessor via the Arduino IDE.

def find_arduino_sketch():
    """
    Searches for an Arduino sketch file (*.ino) within 'arduino/' directories.
    
    Returns:
        str: Path to the first Arduino sketch found, or None if not found.
    """
    # Look for an arduino.ino file specifically within arduino/ directories
    sketch_files = glob.glob('**/arduino/*.ino', recursive=True)
    if not sketch_files:
        print("No Arduino sketch found.")
        return None
    elif len(sketch_files) > 1:
        print("Multiple Arduino sketches found. Using the first one found.")
    return sketch_files[0]

def detect_board_and_port(target_board_name="Arduino Leonardo"):
    """
    Detects the connected Arduino board type and port using arduino-cli.
    
    Args:
        target_board_name (str): The name of the target board to look for.
    
    Returns:
        tuple: (fqbn, port) if found, or (None, None) if not found.
    """
    # Detect the connected board type and port using arduino-cli
    board_list_cmd = "arduino-cli board list"
    result = subprocess.run(board_list_cmd.split(), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to list connected boards:\n{result.stderr}")
        return None, None
    
    lines = result.stdout.splitlines()
    for line in lines:
        if target_board_name.lower() in line.lower() and "/dev" in line:
            parts = line.split()
            port = parts[0]
            fqbn = parts[-2]
            return fqbn, port
    
    print(f"No connected {target_board_name} board found.")
    return None, None

def compile_and_upload(sketch_path, fqbn, port):
    """
    Compiles and uploads the Arduino sketch to the detected board.
    
    Args:
        sketch_path (str): Path to the Arduino sketch.
        fqbn (str): Fully Qualified Board Name.
        port (str): Port where the board is connected.
    
    Returns:
        bool: True if compilation and upload succeed, False otherwise.
    """
    # Compile the Arduino sketch
    compile_cmd = f'arduino-cli compile --fqbn {fqbn} {sketch_path}'
    compile_process = subprocess.run(compile_cmd.split(), capture_output=True, text=True)
    if compile_process.returncode != 0:
        print(f"Compilation failed:\n{compile_process.stderr}")
        return False
    else:
        print("Compilation succeeded.")
    
    # Upload the compiled sketch to the board
    upload_cmd = f'arduino-cli upload -p {port} --fqbn {fqbn} {sketch_path}'
    upload_process = subprocess.run(upload_cmd.split(), capture_output=True, text=True)
    if upload_process.returncode != 0:
        print(f"Upload failed:\n{upload_process.stderr}")
        return False
    else:
        print("Upload succeeded.")
        return True

def run():
    """
    Main function to run the entire process of finding, compiling, and uploading the Arduino sketch.
    """
    # Find the Arduino sketch
    arduino_sketch_path = find_arduino_sketch()
    if not arduino_sketch_path:
        print("Arduino sketch not found. Exiting.")
        exit(1)
    
    # Detect the board type and port
    board_type, port = detect_board_and_port()
    if not board_type or not port:
        print("Failed to detect board type or port. Exiting.")
        exit(1)
    
    # Compile and upload the Arduino sketch
    if compile_and_upload(arduino_sketch_path, board_type, port):
        print("Arduino sketch compiled and uploaded successfully.")
    else:
        print("Failed to compile or upload the Arduino sketch.")

if __name__ == "__main__":
    run()
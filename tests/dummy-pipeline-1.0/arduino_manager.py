import subprocess
import os
import glob

def find_arduino_sketch():
    # Look for an arduino.ino file specifically within arduino/ directories
    sketch_files = glob.glob('**/arduino/*.ino', recursive=True)
    if not sketch_files:
        print("No Arduino sketch found.")
        return None
    elif len(sketch_files) > 1:
        print("Multiple Arduino sketches found. Using the first one found.")
    return sketch_files[0]

def detect_board_and_port(target_board_name="Arduino Leonardo"):
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
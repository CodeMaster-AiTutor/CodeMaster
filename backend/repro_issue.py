import docker
import os
import time
import shutil

# Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp_test_repro")
os.makedirs(TEMP_DIR, exist_ok=True)

# Create Java file
JAVA_CODE = """
public class Test {
    public static void main(String[] args) throws Exception {
        System.out.println("START");
        for(int i=0; i<5; i++) {
            System.out.println("Count: " + i);
            Thread.sleep(500);
        }
        System.out.println("END");
    }
}
"""
with open(os.path.join(TEMP_DIR, "Test.java"), "w") as f:
    f.write(JAVA_CODE)

# Compile
print("Compiling...")
# We assume javac is in path or use docker to compile
client = docker.from_env()
try:
    client.containers.run(
        "codemaster-java17:local",
        "javac Test.java",
        volumes={TEMP_DIR: {"bind": "/app/workspace", "mode": "rw"}},
        working_dir="/app/workspace",
        remove=True
    )
    print("Compilation successful.")
except Exception as e:
    print(f"Compilation failed: {e}")
    exit(1)

# Run
print("Running container...")
try:
    container = client.containers.create(
        image="codemaster-java17:local",
        command=["/usr/bin/stdbuf", "-o0", "-e0", "/opt/jdk-17.0.12/bin/java", "-cp", "/app/workspace", "Test"],
        volumes={TEMP_DIR: {"bind": "/app/workspace", "mode": "rw"}},
        working_dir="/app/workspace",
        stdin_open=True,
        tty=True, # Terminal uses TTY usually? Wait, terminal_sessions sets tty=True?
        detach=True
    )
    
    # Check if terminal_sessions.py uses tty=True. 
    # It sets tty=True, stdin_open=True, detach=True.
    
    container.start()
    print(f"Container started: {container.id}")
    
    # Attach socket
    # This mimics terminal_sessions.py attach_socket
    socket = client.api.attach_socket(
        container.id,
        params={"stdin": 1, "stdout": 1, "stderr": 1, "stream": 1, "logs": 1}
    )
    
    # Windows Npipe fix check
    if hasattr(socket, '_sock'):
        print("Socket has _sock (Linux/Mac behavior)")
        sock = socket._sock
    else:
        print("Socket does NOT have _sock (Windows behavior)")
        sock = socket
        
    sock.setblocking(False)
    
    print("Reading output...")
    start_time = time.time()
    while time.time() - start_time < 5:
        try:
            chunk = sock.recv(4096)
            if chunk:
                print(f"Received: {chunk}")
            else:
                print("EOF")
                break
        except BlockingIOError:
            time.sleep(0.1)
        except Exception as e:
            print(f"Error reading: {e}")
            break
            
    container.stop()
    container.remove()
    
except Exception as e:
    print(f"Run failed: {e}")
finally:
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

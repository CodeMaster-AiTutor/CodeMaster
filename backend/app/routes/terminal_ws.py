import time
import threading
import queue
from flask import request, current_app
from app import sock
from app.services.terminal_sessions import get_terminal_manager


@sock.route("/ws/terminal")
def terminal_socket(ws):
    logger = current_app.logger
    session_id = request.args.get("sessionId")
    token = request.args.get("token")
    logger.info(f"[WS_DEBUG] Connection attempt sessionId={session_id} has_token={bool(token)}")
    if not session_id:
        logger.warning("[WS_DEBUG] Reject missing sessionId")
        ws.send("Missing sessionId")
        return
    manager = get_terminal_manager()
    session = manager.get_session(session_id)
    if not session:
        logger.warning("[WS_DEBUG] Reject invalid session")
        ws.send("Session invalid")
        return
    logger.info(f"[WS_DEBUG] Session found container_id={session.container_id} active={session.active}")
    if manager.require_auth:
        logger.info("[WS_DEBUG] Auth required")
        user = manager.resolve_user(token)
        if not user or (session.user_id and user.id != session.user_id):
            logger.warning("[WS_DEBUG] Reject unauthorized")
            ws.send("Unauthorized")
            return
        logger.info(f"[WS_DEBUG] Auth ok user_id={user.id}")
    else:
        logger.info("[WS_DEBUG] Auth disabled")
    session.touch()
    try:
        container = manager.docker_client.containers.get(session.container_id)
        logger.info(f"[WS_DEBUG] Container status {container.status}")
        if container.status != 'running':
            logs = container.logs(stdout=True, stderr=True).decode('utf-8', errors='replace')
            if logs:
                ws.send(logs)
            ws.send(f"\r\nContainer exited with status: {container.status}\r\n")
            manager.stop_session(session_id)
            return
    except Exception as e:
        logger.error(f"[WS_DEBUG] Container check failed: {e}")
        manager.stop_session(session_id)
        return

    # On Windows with Docker Desktop, attach_socket returns a distinct socket object
    # that might need special handling.
    attach_socket = manager.attach_socket(session_id)
    if not attach_socket:
        logger.error("[WS_DEBUG] Socket attach failed")
        ws.send("Unable to attach to session")
        return

    logger.info(f"[WS_DEBUG] Starting bidirectional loop for session {session_id}")
    output_queue = queue.Queue()
    stop_event = threading.Event()
    docker_closed = False

    def docker_reader():
        while not stop_event.is_set():
            try:
                chunk = attach_socket.recv(4096)
                if chunk:
                    output_queue.put(chunk)
                else:
                    time.sleep(0.01)
            except BlockingIOError:
                time.sleep(0.01)
            except TimeoutError:
                time.sleep(0.01)
            except Exception as e:
                if "The pipe has been ended" in str(e) or "109" in str(e):
                    logger.info("Docker pipe ended")
                    output_queue.put(None)
                    return
                if "timed out" in str(e):
                    time.sleep(0.01)
                else:
                    logger.error(f"Docker read error (ignoring): {e}")
                    time.sleep(0.01)

    reader_thread = threading.Thread(target=docker_reader, daemon=True)
    reader_thread.start()
    
    try:
        while True:
            # Check session status
            if not session.active:
                current_app.logger.info("Session inactive, stopping loop")
                break
                
            try:
                while True:
                    chunk = output_queue.get_nowait()
                    if chunk is None:
                        docker_closed = True
                        break
                    logger.info(f"[WS_DEBUG] Docker->WS bytes={len(chunk)} preview={chunk[:100]!r}")
                    session.output_bytes += len(chunk)
                    session.touch()
                    try:
                        ws.send(chunk)
                        logger.info("[WS_DEBUG] Sent to WebSocket")
                    except Exception as e:
                        logger.error(f"WebSocket send failed: {e}")
                        docker_closed = True
                        break
            except queue.Empty:
                pass
            if docker_closed:
                break

            # 2. Read from WebSocket (Input)
            try:
                # Check for input with a very short timeout
                # flask-sock / simple-websocket receive() supports timeout
                message = ws.receive(timeout=0.01)
                
                if message is not None:
                    payload = message if isinstance(message, (bytes, bytearray)) else str(message).encode("utf-8")
                    if payload:
                        # Normalize line endings
                        if b'\r' in payload:
                            payload = payload.replace(b'\r', b'\n')
                        
                        logger.info(f"WebSocket Input: {payload!r}")
                        session.touch()
                        
                        # Send to Docker
                        total_sent = 0
                        while total_sent < len(payload):
                            try:
                                sent = attach_socket.send(payload[total_sent:])
                                if sent == 0:
                                    raise RuntimeError("Socket connection broken")
                                total_sent += sent
                            except BlockingIOError:
                                time.sleep(0.01)
                                continue
            except Exception as e:
                # Timeout is expected if no input
                # But we need to distinguish timeout from error
                # simple-websocket raises specific errors or returns None?
                # Usually it just raises a timeout exception or similar.
                # If it's a timeout, we just continue.
                pass
            
            # Small sleep to prevent CPU hogging
            time.sleep(0.01)

    except Exception as e:
        logger.error(f"Main loop error: {e}")
    finally:
        stop_event.set()
        if reader_thread.is_alive():
            reader_thread.join(timeout=0.2)
        logger.info(f"Cleaning up session {session_id}")
        manager.stop_session(session_id)

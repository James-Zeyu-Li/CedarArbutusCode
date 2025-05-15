import socket
import sys


def check_grpc(host='127.0.0.1', port=5050):
    s = socket.socket()
    try:
        s.settimeout(5)
        s.connect((host, port))
        print(f"Connected to {host}:{port} successfully.")
        return True
    except Exception as e:
        print(f"Failed to connect to {host}:{port}. Exception: {e}")
        return False
    finally:
        s.close()


if __name__ == '__main__':
    if not check_grpc():
        sys.exit(1)

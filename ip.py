import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# Di bagian app.run() atau route
print(f"🌐 Local IP: {get_local_ip()}")
print(f"🌐 Access URL: http://{get_local_ip()}:5000")
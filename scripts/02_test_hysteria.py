# scripts/02_test_hysteria.py

import subprocess
import json
from pathlib import Path
import tempfile
import re
import time
from utils import get_proxies_from_file

def get_proxy_latency(proxy_config_path: str, hysteria_client_path: str) -> float | None:
    """
    برای یک پراکسی که اتصالش تایید شده، پینگ را اندازه‌گیری می‌کند.
    """
    try:
        command = [hysteria_client_path, "ping", "-c", proxy_config_path]
        process = subprocess.run(command, capture_output=True, text=True, timeout=15)
        if process.returncode == 0 and "Ping:" in process.stdout:
            match = re.search(r"Ping:\s*([\d\.]+\s*ms)", process.stdout)
            if match:
                ping_str = match.group(1).replace(" ", "")
                return float(ping_str.replace("ms", ""))
    except Exception:
        return None
    return None

def test_hysteria_proxy_real_connection(proxy: str, hysteria_client_path: str) -> dict | None:
    """
    یک پراکسی را با برقراری اتصال واقعی از طریق آن به یک سایت خارجی تست می‌کند.
    """
    if not (proxy.startswith("hysteria2://") or proxy.startswith("hy2://")):
        print(f"INFO: پراکسی نادیده گرفته شد (فرمت نامعتبر): {proxy[:50]}...")
        return None

    config = {"server": proxy, "insecure": True}
    client_process = None
    temp_config_path = ""

    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_config_file:
            json.dump(config, temp_config_file)
            temp_config_path = temp_config_file.name

        print(f"🧪 تست اتصال واقعی: {proxy[:60]}...")

        # 1. کلاینت Hysteria را در پس‌زمینه اجرا کن
        client_command = [hysteria_client_path, "client", "-c", temp_config_path]
        client_process = subprocess.Popen(client_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3) # به کلاینت فرصت بده تا اجرا شود

        # 2. با curl از طریق پراکسی محلی به اینترنت وصل شو
        curl_command = [
            "curl",
            "--socks5-hostname", "127.0.0.1:1080", # پراکسی پیش‌فرض Hysteria
            "-I", "-s", # فقط هدرها را بگیر و خروجی را ساکت کن
            "--connect-timeout", "10", # ۱۰ ثانیه مهلت اتصال
            "https://www.youtube.com/" # آدرس تست دلخواه شما
        ]
        
        # 3. نتیجه را بررسی کن
        curl_process = subprocess.run(curl_command, capture_output=True, timeout=15)

        if curl_process.returncode == 0:
            print("✅ اتصال به اینترنت برقرار شد.")
            # 4. اگر اتصال موفق بود، پینگ را بگیر
            latency = get_proxy_latency(temp_config_path, hysteria_client_path)
            if latency is not None:
                print(f"✅ پینگ: {latency:.2f} ms")
                return {"proxy": proxy, "ping": latency}
            else:
                print("⚠️ اتصال برقرار شد ولی پینگ ناموفق بود.")
                return None
        else:
            print("❌ اتصال به اینترنت از طریق پراکسی ناموفق بود.")
            return None

    finally:
        # 5. در هر صورت، پروسه کلاینت را ببند
        if client_process:
            client_process.terminate()
            client_process.wait()
        # فایل کانفیگ موقت را پاک کن
        if temp_config_path and Path(temp_config_path).exists():
            Path(temp_config_path).unlink()

def main():
    print("\n🚀 شروع تست اتصال واقعی پراکسی‌های Hysteria...")
    input_file = Path("output/fetched_hysteria.txt")
    output_file = Path("output/tested_hysteria.json")
    hysteria_client_path = "./hysteria-linux-amd64"

    if not Path(hysteria_client_path).exists():
        print(f"❌ فایل کلاینت Hysteria یافت نشد!")
        return
        
    proxies_to_test = get_proxies_from_file(input_file)
    print(f"تعداد {len(proxies_to_test)} پراکسی برای تست یافت شد.")
    
    working_proxies = []
    for proxy in proxies_to_test:
        result = test_hysteria_proxy_real_connection(proxy, hysteria_client_path)
        if result:
            working_proxies.append(result)
        print("-" * 30)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(working_proxies, f, indent=2)
        
    print(f"\n✅ تست کامل شد. {len(working_proxies)} پراکسی سالم و کاربردی یافت و در {output_file} ذخیره شد.")

if __name__ == "__main__":
    main()

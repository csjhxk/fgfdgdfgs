# scripts/02_test_hysteria.py

import subprocess
import json
from pathlib import Path
import tempfile
import re
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from utils import get_proxies_from_file

MAX_WORKERS = 20
CONNECTION_TEST_URL = "https://www.youtube.com/"
MIN_PING_MS = 10
MAX_PING_MS = 3000

def get_proxy_latency(proxy_config_path: str, hysteria_client_path: str) -> float | None:
    try:
        command = [hysteria_client_path, "ping", "-c", proxy_config_path, "--timeout", "8s"]
        process = subprocess.run(command, capture_output=True, text=True, timeout=10)
        if process.returncode == 0 and "Ping:" in process.stdout:
            match = re.search(r"Ping:\s*([\d\.]+\s*ms)", process.stdout)
            if match:
                ping_str = match.group(1).replace(" ", "")
                return float(ping_str.replace("ms", ""))
    except Exception:
        pass
    return None

def test_single_proxy(proxy: str, port: int, hysteria_client_path: str) -> dict | None:
    if not (proxy.startswith("hysteria2://") or proxy.startswith("hy2://")):
        return None

    listen_address = f"127.0.0.1:{port}"
    config = {
        "server": proxy,
        "insecure": True,
        "socks5": {"listen": listen_address},
        "logLevel": "debug" # ✅ لاگ‌ها را در حالت دیباگ قرار می‌دهیم
    }
    client_process = None
    temp_config_path = ""
    client_log_path = ""

    try:
        # ✅ فایل‌های لاگ و کانفیگ مجزا برای هر ترد
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_config_file, \
             tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log') as temp_log_file:
            json.dump(config, temp_config_file)
            temp_config_path = temp_config_file.name
            client_log_path = temp_log_file.name

        client_command = [hysteria_client_path, "client", "-c", temp_config_path]
        
        # ✅✅✅ تغییر کلیدی: لاگ‌های کلاینت را در یک فایل ذخیره می‌کنیم
        with open(client_log_path, 'w') as log_file:
            client_process = subprocess.Popen(client_command, stdout=log_file, stderr=log_file)
        
        time.sleep(2)

        curl_command = [
            "curl", "--socks5-hostname", listen_address,
            "-s", "--connect-timeout", "8", "--max-time", "10",
            CONNECTION_TEST_URL
        ]
        curl_process = subprocess.run(curl_command, capture_output=True, text=True, timeout=12)

        if curl_process.returncode == 0 and curl_process.stdout.strip():
            latency = get_proxy_latency(temp_config_path, hysteria_client_path)
            if latency and MIN_PING_MS < latency < MAX_PING_MS:
                print(f"✅ پراکسی موفق: {proxy[:40]}... | پینگ: {latency:.2f} ms")
                return {"proxy": proxy, "ping": latency}
        else:
            # ✅✅✅ اگر تست ناموفق بود، لاگ کلاینت را می‌خوانیم و نمایش می‌دهیم
            print(f"❌ اتصال ناموفق برای: {proxy[:60]}...")
            time.sleep(0.5) # فرصت می‌دهیم تا لاگ کامل نوشته شود
            with open(client_log_path, 'r') as log_file:
                client_logs = log_file.read().strip()
                if client_logs:
                    print(f"--- لاگ کلاینت Hysteria ---\n{client_logs}\n--------------------------")
                else:
                    print("--- لاگ کلاینت Hysteria خالی بود ---")

    except Exception as e:
        print(f"### خطای استثنا در پایتون: {e} ###")
    finally:
        if client_process:
            client_process.terminate()
            client_process.wait()
        if temp_config_path and Path(temp_config_path).exists():
            Path(temp_config_path).unlink()
        if client_log_path and Path(client_log_path).exists():
            Path(client_log_path).unlink()
    
    return None

def main():
    print(f"🚀 شروع تست پراکسی‌ها با {MAX_WORKERS} ترد همزمان (حالت دیباگ)...")
    input_file = Path("output/fetched_hysteria.txt")
    output_file = Path("output/tested_hysteria.json")
    hysteria_client_path = "./hysteria-linux-amd64"
    
    proxies_to_test = get_proxies_from_file(input_file)
    print(f"تعداد {len(proxies_to_test)} پراکسی برای تست یافت شد.")
    
    working_proxies = []
    ports = range(10800, 10800 + len(proxies_to_test))

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_proxy = executor.map(test_single_proxy, proxies_to_test, ports, repeat(hysteria_client_path))
        for result in future_to_proxy:
            if result:
                working_proxies.append(result)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(working_proxies, f, indent=2)
        
    print(f"\n✅ تست کامل شد. {len(working_proxies)} پراکسی سالم یافت و در {output_file} ذخیره شد.")

if __name__ == "__main__":
    main()

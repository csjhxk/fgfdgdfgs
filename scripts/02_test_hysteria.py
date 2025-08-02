# scripts/02_test_hysteria.py

import subprocess
import json
from pathlib import Path
import tempfile
import re

def get_proxies_from_file(file_path: Path) -> list[str]:
    """پراکسی‌ها را از یک فایل متنی می‌خواند."""
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def test_hysteria_proxy(proxy: str, hysteria_client_path: str) -> dict | None:
    """
    یک پراکسی Hysteria را با استفاده از کلاینت رسمی تست کرده و نتیجه را برمی‌گرداند.
    """
    if not proxy.startswith("hysteria2://"):
        print(f"⚠️  پراکسی نادیده گرفته شد (فرمت نامعتبر): {proxy[:30]}...")
        return None

    # ساخت یک فایل کانفیگ موقت برای کلاینت
    config = {
        "server": proxy,
        "insecure": True, # نادیده گرفتن خطاهای TLS
    }
    
    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=True, suffix='.json') as temp_config_file:
            json.dump(config, temp_config_file)
            temp_config_file.flush() # اطمینان از نوشته شدن فایل روی دیسک

            print(f"🧪 تست پراکسی: {proxy[:40]}...")
            
            # اجرای کلاینت در حالت بنچمارک برای گرفتن پینگ
            process = subprocess.run(
                [hysteria_client_path, "client", "-c", temp_config_file.name, "--benchmark-speed"],
                capture_output=True,
                text=True,
                timeout=20  # ۲۰ ثانیه مهلت برای هر تست
            )

            if process.returncode == 0 and "ms" in process.stdout:
                # استخراج پینگ (latency) با استفاده از عبارت منظم (Regex)
                match = re.search(r"Latency:\s*([\d\.]+\s*ms)", process.stdout)
                if match:
                    ping_str = match.group(1).replace(" ", "") # "123.45 ms" -> "123.45ms"
                    ping_ms = float(ping_str.replace("ms", ""))
                    print(f"✅ موفق! پینگ: {ping_ms:.2f} ms")
                    return {"proxy": proxy, "ping": ping_ms}

            print(f"❌ ناموفق. خروجی: {process.stderr or process.stdout}")
            return None

    except subprocess.TimeoutExpired:
        print("❌ تست به دلیل پایان زمان مهلت ناموفق بود.")
        return None
    except Exception as e:
        print(f"❌ خطای استثنا: {e}")
        return None

def main():
    print("\n🚀 شروع تست پینگ واقعی پراکسی‌های Hysteria...")
    input_file = Path("output/fetched_hysteria.txt")
    output_file = Path("output/tested_hysteria.json")
    hysteria_client_path = "./hysteria-linux-amd64" # مسیر فایل کلاینت

    proxies_to_test = get_proxies_from_file(input_file)
    print(f"تعداد {len(proxies_to_test)} پراکسی برای تست یافت شد.")
    
    working_proxies = []
    for proxy in proxies_to_test:
        result = test_hysteria_proxy(proxy, hysteria_client_path)
        if result:
            working_proxies.append(result)
    
    # ذخیره نتایج در یک فایل JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(working_proxies, f, indent=2)
        
    print(f"\n✅ تست کامل شد. {len(working_proxies)} پراکسی سالم یافت و در {output_file} ذخیره شد.")

if __name__ == "__main__":
    main()

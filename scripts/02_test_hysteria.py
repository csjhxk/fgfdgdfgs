# scripts/02_test_hysteria.py

import subprocess
import json
from pathlib import Path
import tempfile
import re
from utils import get_proxies_from_file

def test_hysteria_proxy(proxy: str, hysteria_client_path: str) -> dict | None:
    """
    یک پراکسی Hysteria را با استفاده از کلاینت رسمی تست کرده و نتیجه را برمی‌گرداند.
    """
    # هر دو فرمت معتبر hy2 و hysteria2 را می‌پذیریم
    if not (proxy.startswith("hysteria2://") or proxy.startswith("hy2://")):
        print(f"⚠️  پراکسی نادیده گرفته شد (فرمت نامعتبر): {proxy[:50]}...")
        return None

    # یک فایل کانفیگ موقت برای کلاینت ایجاد می‌کنیم
    config = {
        "server": proxy,
        "insecure": True, # برای جلوگیری از خطای سرتیفیکیت در تست
    }
    
    try:
        # از فایل موقت استفاده می‌کنیم تا کانفیگ هر پراکسی جدا باشد
        with tempfile.NamedTemporaryFile(mode='w+', delete=True, suffix='.json') as temp_config_file:
            json.dump(config, temp_config_file)
            temp_config_file.flush() # اطمینان از نوشته شدن کامل فایل روی دیسک

            print(f"🧪 تست پراکسی: {proxy[:60]}...")
            
            # استفاده از دستور صحیح "bench" برای تست پینگ
            command = [
                hysteria_client_path,
                "bench",
                "-c",
                temp_config_file.name
            ]

            process = subprocess.run(
                command,
                capture_output=True, # خروجی و خطا را ذخیره کن
                text=True,           # خروجی را به صورت متن (string) بخوان
                timeout=20           # مهلت ۲۰ ثانیه‌ای برای هر تست
            )

            # بررسی می‌کنیم که آیا تست موفق بوده و عبارت "Ping:" در خروجی وجود دارد
            if process.returncode == 0 and "Ping:" in process.stdout:
                # با استفاده از Regex مقدار پینگ را از خروجی استخراج می‌کنیم
                match = re.search(r"Ping:\s*([\d\.]+\s*ms)", process.stdout)
                if match:
                    ping_str = match.group(1).replace(" ", "") # "123.45 ms" -> "123.45ms"
                    ping_ms = float(ping_str.replace("ms", ""))
                    print(f"✅ موفق! پینگ: {ping_ms:.2f} ms")
                    return {"proxy": proxy, "ping": ping_ms}

            # در صورت بروز خطا، آن را چاپ می‌کنیم تا دیباگ آسان‌تر شود
            error_output = (process.stderr or process.stdout).strip()
            print(f"❌ ناموفق. خروجی: {error_output}")
            return None

    except subprocess.TimeoutExpired:
        print("❌ تست به دلیل پایان زمان مهلت (Timeout) ناموفق بود.")
        return None
    except Exception as e:
        print(f"❌ یک خطای پیش‌بینی‌نشده رخ داد: {e}")
        return None

def main():
    print("\n🚀 شروع تست پینگ واقعی پراکسی‌های Hysteria...")
    input_file = Path("output/fetched_hysteria.txt")
    output_file = Path("output/tested_hysteria.json")
    hysteria_client_path = "./hysteria-linux-amd64" # مسیر فایل کلاینت در ورک‌فلو

    if not Path(hysteria_client_path).exists():
        print(f"❌ فایل کلاینت Hysteria در مسیر {hysteria_client_path} یافت نشد!")
        return
        
    proxies_to_test = get_proxies_from_file(input_file)
    print(f"تعداد {len(proxies_to_test)} پراکسی برای تست یافت شد.")
    
    working_proxies = []
    for proxy in proxies_to_test:
        result = test_hysteria_proxy(proxy, hysteria_client_path)
        if result:
            working_proxies.append(result)
    
    # ذخیره نتایج تست شده در یک فایل JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(working_proxies, f, indent=2)
        
    print(f"\n✅ تست کامل شد. {len(working_proxies)} پراکسی سالم یافت و در {output_file} ذخیره شد.")

if __name__ == "__main__":
    main()

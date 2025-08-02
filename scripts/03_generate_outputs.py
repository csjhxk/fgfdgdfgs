# scripts/03_generate_outputs.py

import json
from pathlib import Path
from base64 import b64encode

def main():
    print("\n🚀 شروع تولید فایل‌های خروجی نهایی...")
    tested_file = Path("output/tested_hysteria.json")
    output_dir = Path("output")

    if not tested_file.exists():
        print(f"❌ فایل نتایج تست {tested_file} یافت نشد. برنامه متوقف می‌شود.")
        return

    with open(tested_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    # مرتب‌سازی پراکسی‌ها بر اساس پینگ (از کم به زیاد)
    sorted_proxies = sorted(results, key=lambda x: x["ping"])
    
    # فقط لینک پراکسی‌ها را استخراج کن
    sorted_proxy_links = [item["proxy"] for item in sorted_proxies]

    # ۱. ذخیره همه پراکسی‌های سالم
    all_path = output_dir / "all.txt"
    with open(all_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted_proxy_links))
    print(f"✅ فایل همه پراکسی‌های سالم در {all_path} ذخیره شد. (تعداد: {len(sorted_proxy_links)})")

    # ۲. ذخیره ۱۰۰ پراکسی برتر
    top_100 = sorted_proxy_links[:100]
    top_100_path = output_dir / "top_100.txt"
    with open(top_100_path, "w", encoding="utf-8") as f:
        f.write("\n".join(top_100))
    print(f"✅ فایل ۱۰۰ پراکسی برتر در {top_100_path} ذخیره شد.")

    # ۳. ذخیره ۵۰۰ پراکسی برتر
    top_500 = sorted_proxy_links[:500]
    top_500_path = output_dir / "top_500.txt"
    with open(top_500_path, "w", encoding="utf-8") as f:
        f.write("\n".join(top_500))
    print(f"✅ فایل ۵۰۰ پراکسی برتر در {top_500_path} ذخیره شد.")

    # ۴. ایجاد و ذخیره لینک اشتراک (Subscription)
    sub_content = "\n".join(sorted_proxy_links)
    encoded_content = b64encode(sub_content.encode("utf-8")).decode("utf-8")
    sub_path = output_dir / "sub.txt"
    with open(sub_path, "w", encoding="utf-8") as f:
        f.write(encoded_content)
    print(f"✅ فایل لینک اشتراک در {sub_path} ایجاد شد.")

if __name__ == "__main__":
    main()

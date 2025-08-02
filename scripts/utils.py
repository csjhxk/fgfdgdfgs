# scripts/utils.py

from pathlib import Path

def get_proxies_from_file(file_path: Path) -> list[str]:
    """پراکسی‌ها را از یک فایل متنی می‌خواند و خطوط خالی را نادیده می‌گیرد."""
    if not file_path.exists():
        print(f"⚠️  فایل ورودی {file_path} یافت نشد.")
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        # فقط خطوطی را برمی‌گرداند که خالی نیستند
        return [line.strip() for line in f if line.strip()]

def save_proxies_to_file(proxies: list[str], output_path: Path):
    """لیستی از پراکسی‌ها را در یک فایل ذخیره می‌کند."""
    # اگر پوشه والد وجود ندارد، آن را ایجاد کن
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(proxies))

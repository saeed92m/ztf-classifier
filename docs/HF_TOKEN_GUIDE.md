# HF_TOKEN — حداقل دسترسی خواندن برای StarEmbed/ZTF_40k

این دیتاست روی Hugging Face به صورت gated/private است (`401 Repository Not Found` بدون توکن).
برای خواندن تنها shard شکست‌خورده روی revision ثابت زیر، یک توکن فقط-خواندن کافی است:

- **Revision ثابت:** `33046797fb619f93a991aa4e38a9dc36f27e2d24` (commit SHA از `https://huggingface.co/api/datasets/StarEmbed/ZTF_40k`)
- **فایل هدف:** `data/train-00001-of-00002.parquet` (حدود چند ده MB، نه کل 432 MB artifact)

## روش امن ساخت توکن (منتظر تایید شما — هنوز secret اضافه نشود)

1. Hugging Face > Settings > Access Tokens > New token
2. Type: **Read** (یا **Fine-grained: Read access to StarEmbed/ZTF_40k only**) — حداقل مجوز
3. Expiration کوتاه (مثلاً 30 روز) و revoke پس از تشخیص
4. در GitHub: `Settings > Secrets and variables > Actions > New repository secret`
   - Name: `HF_TOKEN`
   - Value: توکن کپی‌شده (هرگز در log یا git commit قرار ندهید)

## مصرف در workflow

- فقط در step `3) Download ONLY failing shard` با `env: HF_TOKEN: ${{ secrets.HF_TOKEN }}` در دسترس است
- workflow فقط وضعیت `configured / missing` را لاگ می‌کند؛ نه مقدار توکن و نه طول آن
- `huggingface_hub` به طور خودکار `HF_TOKEN` را می‌خواند؛ هیچ کدی توکن را چاپ نمی‌کند
- بدون secret، workflow به درستی `BLOCKED_GATED_DATASET` گزارش می‌دهد و با کد خروج 0 از مرحله 4 خارج می‌شود (دسترسی مسدود، نه باگ شمارش)

منتظر تایید شما برای افزودن secret هستم؛ تا آن زمان داده واقعی خوانده نمی‌شود.

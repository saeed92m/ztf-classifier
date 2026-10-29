# اجرای آزمون قطعی قاعدهٔ چهار فیلد — کارِ روی لپ‌تاپ شما

**هدف:** پاسخ به تنها سؤال بازِ Issue #170 — آیا قاعدهٔ «چهار فیلد مثبت» عضویت ۷۳۰,۱۸۴ نفری را بازتولید می‌کند یا نه.

**زمان لازم:** حدود ۵ دقیقه (بیشترش دانلود).
**حجم دانلود:** ~۲۲۶ مگابایت.
**چیزی که برمی‌گردانید:** یک فایل JSON کوچک (~۲ کیلوبایت). هیچ داده‌ای آپلود نمی‌شود.

---

## چرا فقط همین دو فایل کافی است

قاعدهٔ مورد بحث تابعی خالص از **چهار ستون متادیتای `table2.dat`** است. پس نه به ۳۵۸ مگابایت نورسنجی، نه به اجرای ۳۰ دقیقه‌ای، و نه به فهرست ۱۱,۶۰۴ شناسهٔ اضافی نیاز ندارد. کافی است:

```
S4 = { Seq در table2 : gmag>0 ∧ rmag>0 ∧ Per-g>0 ∧ Per-r>0 }
P  = عضویت منتشرشده از table4
```

| نتیجه | معنا |
|---|---|
| `S4_only > 0` | قاعده **ابطال** می‌شود: جرمی با چهار فیلد مثبت هست که منتشر نشده |
| `P_only > 0` | قاعده نمی‌تواند تعریف عضویت باشد |
| هر دو صفر | قاعده از نظر مجموعه‌ای هم‌ارز است (**نه اثبات نیت مؤلف**) |

---

## گام ۱ — دانلود

```bash
mkdir -p ~/cpvs && cd ~/cpvs

# جدول ۲ — ۷۸۱,۶۰۲ ردیف، Lrecl 228
curl -L -O https://cdsarc.cds.unistra.fr/ftp/J/ApJS/249/18/table2.dat

# جدول ۴ — ۷۳۰,۱۸۴ ردیف، Lrecl 63
curl -L -O https://cdsarc.cds.unistra.fr/ftp/J/ApJ/932/118/table4.dat
```

اگر CDS در دسترس نبود، آینه‌ها:

```bash
# آینهٔ ژاپن / هاروارد
curl -L -O https://vizier.nao.ac.jp/viz-bin/...    # یا
curl -L -O https://cdsarc.u-strasbg.fr/ftp/J/ApJS/249/18/table2.dat
```

**جایگزین جدول ۲ (Zenodo، با md5 تأییدشده):**

```bash
curl -L -O https://zenodo.org/records/3886372/files/Table2.txt.zip
md5sum Table2.txt.zip     # باید باشد: 24dd4cf138a2687901d64b2d029cc624
unzip Table2.txt.zip
```

> اگر از این مسیر آمدید، فایل حاصل ممکن است `Table2.txt` نام داشته باشد — همان را با `--table2` بدهید. اسکریپت خودش تعداد ردیف و چیدمان را اعتبارسنجی می‌کند؛ اگر نخواند، **با خطای صریح رد می‌کند** و هرگز نتیجهٔ خالیِ به‌ظاهر معتبر نمی‌سازد.

## گام ۲ — بررسی سلامت فایل‌ها

```bash
cd ~/cpvs
wc -l table2.dat table4.dat
# انتظار: 781602 table2.dat   و   730184 table4.dat

ls -l table2.dat table4.dat
# انتظار تقریبی: 178,986,858 بایت  و  46,731,776 بایت
```

> این اندازه‌ها از `(Lrecl + 1) × records` محاسبه شده‌اند، نه از اندازه‌گیری واقعی — من به اینترنت این فایل‌ها دسترسی ندارم. اگر عدد شما متفاوت بود، `wc -l` را معیار بگیرید.

## گام ۳ — اجرای آزمون

```bash
cd ~/cpvs
git clone --depth 1 --branch arena/5d244d9d-ztf-classifier \
    https://github.com/saeed92m/ztf-classifier.git ztf
cd ztf

# اول صحت خودِ اسکریپت را روی داده مصنوعی بسنجید (۱ ثانیه، بدون نیاز به دانلود)
python3 scripts/verify_cpvs_four_field_rule.py --self-test

# بعد اجرای واقعی
python3 scripts/verify_cpvs_four_field_rule.py \
    --table2 ~/cpvs/table2.dat \
    --table4 ~/cpvs/table4.dat \
    --dump-ids
```

روی **ویندوز** (PowerShell)، اگر پایتون دارید و `curl` و `unzip` نیست:

```powershell
cd $HOME
mkdir cpvs; cd cpvs
Invoke-WebRequest -Uri "https://cdsarc.cds.unistra.fr/ftp/J/ApJS/249/18/table2.dat" -OutFile table2.dat
Invoke-WebRequest -Uri "https://cdsarc.cds.unistra.fr/ftp/J/ApJ/932/118/table4.dat" -OutFile table4.dat
# سپس همان دستور python3 بالا را در Git Bash یا WSL اجرا کنید
```

## گام ۴ — نتیجه

سه چیز تولید می‌شود:

| فایل | اندازه | کاربرد |
|---|---|---|
| `cpvs_four_field_report.json` | ~۲ کیلوبایت | **این را برای من بفرستید** |
| `cpvs_four_field_only_ids.txt` | متغیر | شناسه‌هایی که قاعده می‌گیرد ولی منتشر نشده‌اند |
| `cpvs_published_only_ids.txt` | متغیر | اعضای منتشرشده که قاعده ردشان می‌کند |

فقط همان JSON را در چت بفرستید (یا محتوایش را پیست کنید). شناسه‌ها لازم نیست — در JSON هش SHA-256 هر دو مجموعه هست، که برای بازبینی کافی است.

JSON حاوی این‌ها خواهد بود: هش SHA-256 هر دو فایل ورودی، تعداد ردیف‌ها، تعداد هر فیلد تهی، تعداد شکاف‌های `Seq`، تعداد `S4`، تعداد اعضای منتشرشده، اشتراک، دو تفاضل، و هش هر دو مجموعه.

---

## اگر دانلود ممکن نبود

مسیر دوم (سبک‌تر از نظر پهنای باند، ولی نیازمند یک فایل دیگر) — آرشیو Zenodo:

```bash
curl -L -O https://zenodo.org/records/5764899/files/Zenodo.zip
md5sum Zenodo.zip        # باید باشد: 7fc6562d4208cbfa97366351984810e3
unzip Zenodo.zip

python3 scripts/verify_cpvs_four_field_rule.py \
    --table2 ~/cpvs/table2.dat \
    --zenodo-csv 1st_layer.csv
```

`1st_layer.csv` فهرست منتشرشدهٔ مستقل از ناشر است (۷۳۰,۱۸۴ ردیف، ۴۵ ستون). پیوند بر **نام ZTF** انجام می‌شود، نه بر `Seq` — تا دو فضای نام شناسه با هم قاطی نشوند.

---

## آزمون‌های رگرسیون

```bash
python3 -m pytest tests/test_cpvs_four_field_rule.py -q     # ۱۴ تست
python3 scripts/verify_cpvs_four_field_rule.py --self-test  # PASS
```

پوشش: چیدمان بایت، نشانگر تهی `?=0`، بریدگی ردیف، `Seq` تکراری، `Seq` خارج از بازه، ناسازگاری نام↔`Seq`، تعداد ردیف اشتباه، مسیر Zenodo، و اینکه خروجی خالیِ به‌ظاهر معتبر **ممکن نباشد**.

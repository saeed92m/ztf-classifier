# برنامه آزمون پذیرش Windows Pre-release پارک

**وضعیت:** TEST PLAN · نتیجه آزمون‌ها هنوز ثبت نشده است  
**نسخه هدف:** `0.1.0-preview.1`  
**سیستم هدف:** Windows 10/11 x64  
**ردیاب:** [Issue #158](https://github.com/saeed92m/ztf-classifier/issues/158)

این سند روش آزمون را تعریف می‌کند. وجود آن به معنی PASS نیست. هر آزمون باید با تاریخ، نسخه، commit، محیط، نتیجه، log و مدرک ثبت شود.

## 1. ورودی آزمون

- GitHub Pre-release installer.
- SHA-256 checksum و build manifest.
- release notes و user guide.
- Windows clean-machine test environment.
- اتصال اینترنت برای دریافت داده DR24 و نصب Evergreen WebView2 Runtime در صورت نبود آن.

## 2. پیش‌شرط‌ها

1. از یک Windows x64 تمیز یا VM snapshot استفاده کنید.
2. کاربر آزمون نباید Python، pip، Git یا ابزار توسعه نصب کرده باشد.
3. کاربر عادی و بدون دسترسی Administrator را در اولویت قرار دهید.
4. نسخه Windows، architecture، RAM، فضای خالی و WebView2 Runtime را ثبت کنید.
5. قبل از اجرا، checksum را بررسی کنید.
6. installer فعلی unsigned است. این وضعیت باید در گزارش ثبت شود. checksum جایگزین code signing نیست.

## 3. آزمون‌های Installer

| ID | آزمون | روش | معیار PASS |
|---|---|---|---|
| W01 | SHA-256 | `Get-FileHash .\ZTFClassifier-0.1.0-preview.1-Setup.exe -Algorithm SHA256` | مقدار با `SHA256SUMS.txt` یکسان باشد |
| W02 | x64 gate | اجرای installer روی Windows x64 | ادامه نصب |
| W03 | 32-bit rejection | آزمون در VM 32-bit، اگر در دسترس باشد | installer با پیام روشن نصب را متوقف کند |
| W04 | WebView2 present | اجرای installer با Runtime موجود | نصب بدون دریافت مجدد Runtime |
| W05 | WebView2 absent, online | اجرای installer با Runtime حذف‌شده در VM آزمون | bootstrapper دارای امضای معتبر Microsoft اجرا شود و Runtime نصب شود |
| W06 | WebView2 absent, offline | قطع اینترنت و اجرای installer | نصب ناقص انجام نشود؛ خطای روشن و قابل اقدام نمایش داده شود |
| W07 | per-user install | اجرای installer با کاربر عادی | نصب در LocalAppData بدون نیاز به elevation |
| W08 | Start Menu/Desktop shortcuts | بررسی shortcutها | shortcutها به executable نصب‌شده اشاره کنند |
| W09 | repeat install | نصب دوباره همان نسخه | رفتار idempotent یا پیام روشن؛ فایل داده کاربر حفظ شود |

**محدودیت:** WebView2 Evergreen bootstrapper برای دریافت Runtime به اینترنت نیاز دارد. نصب آفلاین Runtime جداگانه و در این نسخه تضمین نشده است.

## 4. آزمون اجرای برنامه

| ID | آزمون | روش | معیار PASS |
|---|---|---|---|
| W10 | Launch | اجرا از Start Menu | پنجره برنامه باز شود و blank screen نداشته باشد |
| W11 | local API binding | بررسی listener برنامه | فقط loopback، نه `0.0.0.0` یا IP شبکه |
| W12 | API authentication | درخواست بدون token و با token نامعتبر | endpointهای `/v1` رد شوند |
| W13 | WebView navigation | لینک داخلی، لینک خارجی و URI scheme | داخلی در برنامه؛ خارجی در مرورگر سیستم؛ scheme ناشناخته مسدود |
| W14 | restart | بستن و اجرای مجدد | برنامه بدون port conflict بالا بیاید |
| W15 | no developer tools | بررسی مسیر کاربر | برای اجرای عادی Python/Git/terminal لازم نباشد |

## 5. آزمون گردش‌کار داده

1. یک workspace جدید بسازید.
2. یک یا چند OID از cohort تأییدشده پارک وارد کنید.
3. DR24 query را اجرا کنید.
4. تعداد requested، returned و missing را ثبت کنید.
5. source, release, query, timestamps و per-object hash را بررسی کنید.
6. نمودار و descriptive summary را بازبینی کنید.
7. خروجی JSON را ذخیره کنید.
8. workspace را ببندید و دوباره باز کنید.
9. export و provenance را با ورودی اصلی مقایسه کنید.

**محدودیت علمی:** این مسیر در وضعیت فعلی raw/descriptive است. آن را classification، model feature، calibrated probability یا anomaly detection معرفی نکنید. این موارد فقط پس از تکمیل Gateهای علمی متناظر قابل پذیرش‌اند.

## 6. آزمون Uninstall و حفظ داده

| ID | آزمون | معیار PASS |
|---|---|---|
| W16 | Uninstall | executable، shortcuts و install directory حذف شوند |
| W17 | User data preservation | workspace، logs و exportهای کاربر حذف نشوند |
| W18 | Reinstall | نصب مجدد بتواند داده‌های قبلی کاربر را بدون corruption باز کند |

## 7. شواهد الزامی هر آزمون

برای هر ID ثبت کنید:

- Test ID و PASS/FAIL/BLOCKED/NOT RUN.
- تاریخ و زمان UTC.
- Windows edition، version/build و architecture.
- RAM، فضای خالی و نام محیط آزمون.
- desktop version، source commit و installer SHA-256.
- WebView2 Runtime version و نحوه نصب آن.
- log، screenshot و مسیر artifact.
- خطا، محدودیت و اقدام اصلاحی.

هیچ آزمون NOT RUN یا SKIPPED را PASS تلقی نکنید.

## 8. محدودیت‌های انتشار

- installer تا زمان امضای کد، UNSIGNED است.
- checksum فقط یکپارچگی فایل را بررسی می‌کند؛ هویت ناشر را اثبات نمی‌کند.
- upload عمومی artifact تا زمان تأیید کتبی شرایط ارزیابی پارک مجاز نیست.
- انتشار Pre-release به معنی تأیید علمی یا پذیرش پارک نیست.

## 9. شرط پذیرش نهایی

W01–W18 باید با شواهد مناسب اجرا شوند. گردش‌کار داده باید روی cohort تأییدشده پارک کار کند. گزارش نصب، اجرا، export و حفظ داده باید کامل باشد. سپس Founder / Project Owner نسخه را برای ارائه به پارک تأیید می‌کند.

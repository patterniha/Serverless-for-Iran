# سرورلس برای ایران

**"سرورلس برای ایران"** حاصل مجموعه ای از دستاوردها در حوزه‌ی دسترسی به اینترنت **بدون فیلتر** و **بدون تحریم** و **بدون تبلیغ** است؛ که بدون نیاز به هیچ سروری کاربر را قادر می سازد تا حدالامکان از اینترنت آزاد و بدون محدودیت استفاده کند.

https://t.me/projectXhttp

https://t.me/patterniha



# نکات استفاده

۱. کانفیگ سرورلس برای اجرا نیاز به هسته Xray-core حداقل ورژن 25.12.8 دارد (حداقل v2rayNG v1.10.31)

۲. برای بایپس کامل وب‌سایتهای ایرانی و همچنین حذف کاملتر تبلیغات وب‌سایتهای ایرانی بهتر است از فایلهای جئو Chocolate4U استفاده کنید (در v2rayNG در قسمت Asset files لیست Chocolate4U را انتخاب کرده و اپدیت را بزنید)

۳. کل رنج آی پی های تلگرام به طور کلی فیلتر هستند بنابراین برای استفاده از تلگرام نیاز به پروکسی تلگرام دارید.

۴. برخی رنج آی پی های ورژن ۴ اینستاگرام نیز فیلتر هستند بنابراین در صورت نداشتن ipv6 ممکن است اینستاگرام با اختلال همراه باشد. **برای فعال کردن ipv6 باید تیک "Prefer IPv6" را در اپ v2rayNG فعال کنید همچنین در صورتی که از اینترنت همراه استفاده میکنید باید ipv6 را در قسمت Access-Point گوشی خود فعال کنید.**

۵. همچنین hev-socks5-tunnel عملکرد بسیار بهتری از badvpn-tun2socks در برنامه v2rayNG دارد بنابراین تیک Enable New TUN Feature را نیز در تنظیمات برنامه v2rayNG فعال کنید. البته برای عملکرد درست UDP-Read/write-timeout باید حداکثر ۶۰ ثانیه باشد که از نسخه  v1.10.32 به بعد این مورد رعایت شده است.


۶. سعی شده بهترین کانفیگ متناسب با تمام isp ها قرار داده شود به هر حال مواردی که احتمالا نیاز به تغییر دارند با کامنت در کانفیگها مشخص شده اند مانند نوع فرگمنت و ...(کامنتها در کانفیگهای دستی وجود دارند و در کانفیگهای Subscription امکان درج کامنت وجود ندارد)

۷. تفاوت نسخه های Serverless و Serverless-dynx و ... در آدرس dns تحریم شکن میباشد؛ نسخه Serverless تحریم شکنی ندارد؛ سایر نسخه ها از تحریم شکنی با همان نام استفاده میکنند (مثلا Serverless-dynx از تحریم شکن dynx استفاده میکند)؛ همچنین تحریم شکن shatel (با نام Serverless-shatel) تنها روی اینترنت های شاتل (اینترنت ثابت شاتل و شاتل موبایل) کار میکند ولی سایر تحریم شکن ها محدودیتی ندارند و روی تمام اینترنت ها کار میکنند.

۸. در اندروید برای استفاده از dns ضد تحریم و دور زدن تحریمها باید Private DNS در تنظیمات اندروید و Use secure DNS در تنظیمات کروم خاموش باشد.


۹. در اپ v2rayNG بهتر است کانفیگها به صورت Subscription وارد شود تا در صورت آپدیت کانفیگها به صورت اتوماتیک برای شما هم اپدیت شود. موقع اضافه کردن: remarks را اسمی دلخواه قرار دهید؛ URL را آدرس Subscription قرار دهید؛ تیک automatic update را فعال کنید؛ و در آخر آپدیت را بزنید (همچنین برای آپدیت اتوماتیک باید آن را در تنظیمات برنامه نیز فعال کنید)


**آدرس Subscription تمامی نسخه ها:**


**https://raw.githubusercontent.com/patterniha/Serverless-for-Iran/refs/heads/main/Subscription/Serverless-for-Iran.json**

**آدرس نسخه کامل تست (full matrix):**

**https://raw.githubusercontent.com/patterniha/Serverless-for-Iran/refs/heads/main/Subscription/Serverless-for-Iran-full.json**

**manifest پروفایل‌ها:**

**https://raw.githubusercontent.com/patterniha/Serverless-for-Iran/refs/heads/main/Subscription/profiles-manifest.json**

# نسخه MitM + DomainFronting

بزودی...

# انتخاب پروفایل (نسخه‌های جدید)

ابتدا Subscription پیش‌فرض (curated) را استفاده کنید، نه full matrix.

Start here:

1. `mobile-soft-quic-block-cf`
2. `natA-tlshello-small-quic-block-cf`
3. `natB-stream-small-udp-light-google`
4. `mobile-soft-udp-light-quad9`
5. `legacy-v41-quic-block-cf`

در اسم پروفایل:

- `quic-block` یعنی QUIC/UDP443 بلاک می‌شود تا اپ‌ها سریع‌تر به TCP/TLS برگردند.
- `udp-light` یعنی UDP فعال می‌ماند اما noise بسیار سبک‌تر از حالت قدیمی است.
- `udp-heavy` حالت سنگین قبلی است و فقط برای تست/حالت آزمایشی پیشنهاد می‌شود.
- `cf` / `google` / `quad9` یعنی DNS no-filter روی DoH همان سرویس تنظیم شده است.

# Troubleshooting

## Browser does not open blocked sites

1. `natA-tlshello-small-quic-block-cf`
2. `natB-stream-small-quic-block-google`
3. `mobile-soft-quic-block-quad9`

## Browser works but Android apps fail

1. اول یک `quic-block` تست کنید.
2. بعضی اپ‌ها روی UDP/443 می‌مانند و تا QUIC بلاک نشود به TCP fragmentation سوئیچ نمی‌کنند.

## DNS errors / NXDOMAIN / only some domains fail

1. DNS family را عوض کنید: `cf` یا `google` یا `quad9`
2. Android Private DNS را خاموش کنید.
3. Chrome Secure DNS را خاموش کنید.

## High latency / battery drain / hot phone

1. full/lab را استفاده نکنید.
2. `udp-heavy` را استفاده نکنید.
3. از `mobile-soft-quic-block` یا `mobile-soft-udp-light` استفاده کنید.

## Nothing works on one operator

1. یک Testing Report باز کنید.
2. فقط operator, client, profile, failure type را بفرستید.
3. IP کامل، شماره، هندل، یا اسکرین‌شات شخصی نفرستید.

## Path diagnostics

برای گزارش مسیر/دی‌ان‌اس/گواهی TLS از اسکریپت زیر استفاده کنید:

`scripts/diagnose_path.sh github.com`

این اسکریپت خروجی privacy-safe آماده کپی برای issue می‌دهد.

# نکته امنیتی

این کانفیگ‌ها direct/serverless هستند و ابزار ناشناس‌سازی نیستند. ISP می‌تواند مقصد IP، timing، حجم ترافیک، و الگوهای غیرعادی اتصال را مشاهده کند.

در گزارش‌ها IP کامل، شماره موبایل، یوزرنیم، اسکرین‌شات دارای اطلاعات شخصی، یا هر شناسه قابل ردیابی ارسال نکنید.

# حمایت

`USDT (BEP20)`: 0x76a768B53Ca77B43086946315f0BDF21156bF424

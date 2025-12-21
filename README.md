# سرورلس برای ایران

**"سرورلس برای ایران"** حاصل مجموعه ای از دستاوردها در حوزه‌ی دسترسی به اینترنت **بدون فیلتر** و **بدون تحریم** و **بدون تبلیغ** است؛ که بدون نیاز به هیچ سروری کاربر را قادر می سازد تا حدالامکان از اینترنت آزاد و بدون محدودیت استفاده کند.

https://t.me/projectXhttp

https://t.me/patterniha

# نکات استفاده

۱. کانفیگ سرورلس برای اجرا نیاز به هسته Xray-core حداقل ورژن 25.12.8 دارد (حداقل v2rayNG v1.10.31)

۲. برای بایپس کامل وب‌سایتهای ایرانی و همچنین حذف کاملتر تبلیغات وب‌سایتهای ایرانی بهتر است از فایلهای جئو Chocolate4U استفاده کنید (در v2rayNG در قسمت Asset files لیست Chocolate4U را انتخاب کرده و اپدیت را بزنید)

۳. کل رنج آی پی های تلگرام به طور کلی فیلتر هستند بنابراین برای استفاده از تلگرام نیاز به پروکسی تلگرام دارید.

۴. برخی رنج آی پی های ورژن ۴ اینستاگرام نیز فیلتر هستند بنابراین در صورت نداشتن ipv6 ممکن است اینستاگرام با اختلال همراه باشد. **برای فعال کردن ipv6 باید تیک "Prefer IPv6" را در اپ v2rayNG فعال کنید همچنین در صورتی که از اینترنت همراه استفاده میکنید باید ipv6 را در قسمت Access-Point گوشی خود فعال کنید.**

۵. سعی شده بهترین کانفیگ متناسب با تمام isp ها قرار داده شود به هر حال مواردی که احتمالا نیاز به تغییر دارند با کامنت در کانفیگها مشخص شده اند مانند نوع فرگمنت و ...(کامنتها در کانفیگهای دستی وجود دارند و در کانفیگهای Subscription امکان درج کامنت وجود ندارد)

۶. تفاوت نسخه های Serverless و Serverless-dynx و ... در آدرس dns تحریم شکن میباشد؛ نسخه Serverless تحریم شکنی ندارد؛ سایر نسخه ها از تحریم شکنی با همان نام استفاده میکنند (مثلا Serverless-dynx از تحریم شکن dynx استفاده میکند)؛ همچنین تحریم شکن shatel (با نام Serverless-shatel) تنها روی اینترنت های شاتل (اینترنت ثابت شاتل و شاتل موبایل) کار میکند ولی سایر تحریم شکن ها محدودیتی ندارند و روی تمام اینترنت ها کار میکنند.

۷. در اندروید برای استفاده از dns ضد تحریم و دور زدن تحریمها باید Private DNS در تنظیمات اندروید و Use secure DNS در تنظیمات کروم خاموش باشد.

۸. در اپ v2rayNG بهتر است کانفیگها به صورت Subscription وارد شود تا در صورت آپدیت کانفیگها به صورت اتوماتیک برای شما هم اپدیت شود. موقع اضافه کردن: remarks را اسمی دلخواه قرار دهید؛ URL را آدرس Subscription قرار دهید؛ تیک automatic update را فعال کنید؛ و در آخر آپدیت را بزنید (همچنین برای آپدیت اتوماتیک باید آن را در تنظیمات برنامه نیز فعال کنید)

**آدرس Subscription تمامی نسخه ها:**

**https://raw.githubusercontent.com/patterniha/Serverless-for-Iran/refs/heads/main/Subscription/Serverless-for-Iran.json**

**آدرس کانفیگ‌های بدون کامنت (برای کلاینت‌هایی که با کامنت مشکل دارند مانند Streisand):**

**Subscription (تمامی نسخه‌ها): https://raw.githubusercontent.com/patterniha/Serverless-for-Iran/refs/heads/main/Subscription/Serverless-for-Iran-no-comment.json**

**لیست فایل‌ها به صورت تکی:**

- [Serverless.json](https://raw.githubusercontent.com/patterniha/Serverless-for-Iran/refs/heads/main/Subscription/no-comment/Serverless.json)
- [Serverless-dynx.json](https://raw.githubusercontent.com/patterniha/Serverless-for-Iran/refs/heads/main/Subscription/no-comment/Serverless-dynx.json)
- [Serverless-shatel.json](https://raw.githubusercontent.com/patterniha/Serverless-for-Iran/refs/heads/main/Subscription/no-comment/Serverless-shatel.json)
- [Serverless-vanilla.json](https://raw.githubusercontent.com/patterniha/Serverless-for-Iran/refs/heads/main/Subscription/no-comment/Serverless-vanilla.json)
- [Serverless-zeus.json](https://raw.githubusercontent.com/patterniha/Serverless-for-Iran/refs/heads/main/Subscription/no-comment/Serverless-zeus.json)

# نسخه MitM + DomainFronting

بزودی...

# حمایت

USDT (TRC20): TU5gKvKqcXPn8itp1DouBCwcqGHMemBm8o

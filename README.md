# Trade Exchange — Crop/Commodity Exchange Platform

منصة بورصة محاصيل مبنية كموديول **Odoo 20** (`crop_exchange`).

## الفكرة
- **الإدارة** تضبط قائمة المحاصيل المعتمدة في البورصة (`crop.product`).
- **التاجر/المصدّر** يسجّل كـ `crop.provider` عبر فورم عام، وتوافق عليه الإدارة.
- بعد الاعتماد، يسجّل عروضه (`crop.listing`): محصول من القائمة + كمية + سعر + موقع.
- لوحة عامة `/exchange` بشكل **جدول بورصة**: صف لكل محصول، بمتوسط السعر وعدد العروض المتاحة.
- الضغط على محصول يفتح `/exchange/crop/<id>` — جدول بكل التجار/المصدّرين المعروض أسعارهم لهذا المحصول (الاسم فقط، بدون بيانات تواصل).
- من هناك، الضغط على عرض معيّن يفتح تفاصيله وفورم "طلب اهتمام" (`crop.interest`) — **بدون** الحصول على بيانات تواصل التاجر مباشرة.
- الإدارة تراجع طلبات الاهتمام وتربط المشتري بالتاجر يدوياً.
- الولاية في `crop.listing` حقل `Many2one` على جدول `res.country.state` الافتراضي بأودو (مقيّد بالسودان).

## البنية
```
crop_exchange/
├── models/            # crop.product, crop.provider, crop.listing, crop.interest
├── security/          # groups, ir.rule, ACL
├── controllers/       # public website routes (board, interest form, registration)
├── views/             # backend views + menus + QWeb website templates
├── data/               # seed crop list + daily expiry cron
└── static/src/js/      # small frontend helper (filter auto-submit)
```

## التثبيت (Odoo 20)
1. انسخ مجلد `crop_exchange` إلى مسار الإضافات (`addons_path`) الخاص بسيرفر Odoo 20.
2. فعّل *Developer Mode*، ثم Apps → Update Apps List.
3. ابحث عن **Crop Exchange Platform** وثبّته.
4. بعد التثبيت: Settings → Users → أنشئ مستخدم إدارة وأضفه لمجموعة **Exchange Administrator**.
5. من قائمة *Crop Exchange → Administration → Crop Master List* أضف/راجع المحاصيل.
6. اللوحة العامة متاحة على: `https://<domain>/exchange`
7. فورم تسجيل التاجر: `https://<domain>/exchange/register`

## النطاق المقترح
`trade-exchange.sd` (يُسجَّل عبر الهيئة السودانية لتسجيل النطاقات).

## خطوات لاحقة مقترحة
- ربط موديول BrqSMS الموجود لإشعار الموافقة/طلبات الاهتمام تلقائياً.
- إمكانية فصل الواجهة العامة لاحقاً إلى تطبيق Next.js مستقل يتصل عبر JSON-RPC/REST (كما في معمارية الـ SaaS سابقاً)، مع إبقاء Odoo كـ Backend.

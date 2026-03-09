# 🔐 دليل إعداد بيانات الدخول والإعدادات

**ملف شامل يحتوي على جميع بيانات الدخول والإعدادات المطلوبة**

---

## 📋 بيانات الدخول الافتراضية

### الدخول الأول للتطبيق:

```
البريد الإلكتروني: admin@radar.com
كلمة المرور: admin123
```

⚠️ **تنبيه أمني مهم:** غيّر كلمة المرور بعد أول دخول مباشرة!

---

## 🔑 متغيرات البيئة المطلوبة

### 1️⃣ للتشغيل المحلي (Local Development)

أنشئ ملف باسم `.env` في مجلد المشروع وأضف:

```
# بيانات الدخول
ADMIN_EMAIL=admin@radar.com
ADMIN_PASSWORD=admin123

# مفتاح الأمان
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# مفتاح OpenRouter (اختياري للتطوير)
OPENROUTER_API_KEY=your-openrouter-api-key

# إعدادات الخادم
PORT=5000
HOST=0.0.0.0
```

### 2️⃣ للإنتاج على Railway

أضف هذه المتغيرات في لوحة Railway:

```
ADMIN_EMAIL=admin@radar.com
ADMIN_PASSWORD=your-strong-password-here
SECRET_KEY=generate-random-string-here
FLASK_ENV=production
OPENROUTER_API_KEY=your-openrouter-api-key
DATABASE_URL=postgresql://user:password@host:port/db
```

---

## 🛠️ خطوات الإعداد التفصيلية

### الخطوة 1: تشغيل محلي

```bash
# 1. انسخ المشروع
git clone https://github.com/zlthbolo/Telegram-server.git
cd Telegram-server

# 2. أنشئ بيئة افتراضية
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows

# 3. ثبّت المكتبات
pip install -r requirements.txt

# 4. شغّل التطبيق
python app.py

# 5. افتح المتصفح
# http://localhost:5000
```

### الخطوة 2: تسجيل الدخول

```
البريد: admin@radar.com
كلمة المرور: admin123
```

### الخطوة 3: تغيير كلمة المرور

1. سجّل دخول بـ `admin123`
2. اذهب إلى **"الإعدادات"** (Settings)
3. انقر على **"تغيير كلمة المرور"** (Change Password)
4. أدخل كلمة مرور جديدة قوية
5. احفظ التغييرات

---

## 🔐 كيفية إنشاء كلمة مرور قوية

### معايير كلمة المرور القوية:
- ✅ 20+ حرف على الأقل
- ✅ تحتوي على أحرف كبيرة (A-Z)
- ✅ تحتوي على أحرف صغيرة (a-z)
- ✅ تحتوي على أرقام (0-9)
- ✅ تحتوي على رموز خاصة (!@#$%^&*)

### أمثلة على كلمات مرور قوية:

```
✅ MyT3l3gr@m!R@d@r#2024
✅ Secure$P@ssw0rd!Radar123
✅ T3l3gr@m-R@d@r-2024-Secure!
✅ RadarApp@2024!Secure#Pass
✅ T3l3gr@m$M0nit0r!2024#Sec
```

### كلمات مرور ضعيفة (لا تستخدمها):

```
❌ admin123 (بسيطة جداً)
❌ password (شائعة جداً)
❌ 12345678 (متسلسلة)
❌ qwerty (لوحة المفاتيح)
❌ telegram (اسم التطبيق)
```

---

## 🤖 الحصول على مفتاح OpenRouter API

### الخطوة 1: إنشاء حساب

1. اذهب إلى [openrouter.ai](https://openrouter.ai)
2. انقر **"Sign Up"** أو **"Get Started"**
3. أنشئ حساب جديد

### الخطوة 2: الحصول على المفتاح

1. بعد التسجيل، اذهب إلى **"Keys"** أو **"API Keys"**
2. انقر **"Create New Key"**
3. أعطِ المفتاح اسماً (مثل: "Telegram Radar")
4. انسخ المفتاح الطويل

### الخطوة 3: إضافة المفتاح

**للتطوير المحلي:**
```
أضفه في ملف .env:
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
```

**للإنتاج على Railway:**
```
أضفه في Variables:
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
```

---

## 🗄️ قاعدة البيانات

### SQLite (محلي - افتراضي)
- لا تحتاج لإعدادات إضافية
- الملف: `radar.db` (يُنشأ تلقائياً)

### PostgreSQL (إنتاج - Railway)

Railway سيوفر `DATABASE_URL` تلقائياً:

```
DATABASE_URL=postgresql://user:password@host:port/database
```

لا تحتاج لفعل شيء! النظام يكتشفها تلقائياً.

---

## 📱 إضافة حسابات تليجرام

### الخطوة 1: الحصول على API Credentials

1. اذهب إلى [my.telegram.org](https://my.telegram.org)
2. سجّل دخول برقم هاتفك
3. اضغط **"API Development Tools"**
4. أنشئ تطبيقاً جديداً
5. احصل على:
   - **API ID** (رقم)
   - **API Hash** (نص طويل)

### الخطوة 2: إضافة الحساب في التطبيق

1. سجّل دخول للتطبيق
2. اذهب إلى **"إدارة الحسابات"**
3. أدخل:
   - رقم الهاتف (مثل: 967XXXXXXXXX)
   - API ID
   - API Hash
   - مجموعة الإشعارات (اختياري)
4. انقر **"إضافة حساب"**

### الخطوة 3: التحقق

- النظام سيطلب رمز التحقق من تليجرام
- أدخل الرمز
- إذا كان الحساب محمياً بـ 2FA، أدخل كلمة المرور

---

## 🔍 استكشاف الأخطاء الشائعة

### خطأ: "كلمة المرور خاطئة"

**الحل:**
- تأكد من أنك تستخدم: `admin@radar.com` و `admin123`
- تأكد من عدم وجود مسافات إضافية
- جرّب مسح ذاكرة التخزين المؤقت (Cache)

### خطأ: "Invalid API credentials"

**الحل:**
- تأكد من صحة API ID و API Hash
- تحقق من أنك نسختهما من my.telegram.org
- جرّب إنشاء تطبيق جديد

### خطأ: "OpenRouter API not working"

**الحل:**
- تأكد من صحة المفتاح
- تحقق من أن لديك حصة مجانية متبقية
- جرّب المفتاح على موقع OpenRouter

### خطأ: "Cannot connect to database"

**الحل:**
- للمحلي: تأكد من أن ملف `radar.db` موجود
- للـ Railway: تأكد من أن PostgreSQL قيد التشغيل
- تحقق من `DATABASE_URL` الصحيح

---

## 📝 قائمة التحقق (Checklist)

قبل النشر على Railway:

- [ ] غيّرت `ADMIN_PASSWORD` إلى كلمة مرور قوية
- [ ] حصلت على `OPENROUTER_API_KEY` من openrouter.ai
- [ ] أضفت جميع المتغيرات في Railway
- [ ] اختبرت التطبيق محلياً
- [ ] أضفت حساب تليجرام واحد على الأقل
- [ ] اختبرت إرسال رسالة تجريبية

---

## 🎯 الخطوات السريعة

### للتطوير المحلي:
```bash
git clone https://github.com/zlthbolo/Telegram-server.git
cd Telegram-server
pip install -r requirements.txt
python app.py
# افتح: http://localhost:5000
# البريد: admin@radar.com
# كلمة المرور: admin123
```

### للإنتاج على Railway:
```
1. اذهب إلى railway.app
2. اختر "Deploy from GitHub"
3. اختر "Telegram-server"
4. أضف PostgreSQL
5. أضف المتغيرات (ADMIN_PASSWORD, OPENROUTER_API_KEY, etc)
6. اضغط Deploy
```

---

**كل شيء جاهز الآن! 🎉**

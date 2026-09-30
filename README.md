# NOVA Attendance · Version 2 Beta

แอปต้นแบบมือถือ/คอมพิวเตอร์ที่พัฒนาต่อจากดราฟ 4 และเก็บแยกจากเวอร์ชัน 1

## สิ่งที่อยู่ในเบต้านี้

- แถบนำทาง 3 แท็บตามแบบ: **ประวัติของฉัน / หน้าหลัก / ตั้งค่า**; ไม่มีการเพิ่มแท็บหลักใหม่
- หน้าพนักงาน: เปิดกล้อง, ตรวจว่ามีใบหน้าในกรอบด้วย browser ที่รองรับ, เก็บ event ตัวอย่างใน local storage และแสดงชัดว่าเป็น DEMO
- Admin เพิ่มพนักงาน: ชื่อจริง, ชื่อเล่น, ประเภทพนักงาน, กะ, หมายเหตุ; ปุ่มลงทะเบียนใบหน้าแสดงสถานะปิดไว้
- Admin ขั้นสูง: ภาพรวม/อนุมัติรายการเดโม, จัดการพนักงาน, ตั้งกะ, สถานที่ทำงาน, ปฏิทินวันหยุด และส่งออก CSV ตัวอย่าง
- Apps Script `setupAll()` สร้าง schema ตาม ER ใน Spreadsheet; write API ปิดไว้เพื่อไม่ให้ public caller ปลอมเวลา/คะแนน
- Python Face API ตรวจคุณภาพ/จำนวนใบหน้าได้เมื่อมี MediaPipe task model ที่ผ่านการเลือกและตั้ง token; **การจับคู่ตัวตนและ PAD ยังปิดอยู่**

## 1. เปิดแอปหน้าเว็บในเครื่อง

ต้องมี Node.js 20 หรือใหม่กว่า

```sh
cd "ระบบ/เวอร์ชัน_2_เบต้า"
npm install
npm run dev
```

เปิด URL localhost ที่ Vite แจ้ง กล้องต้องอนุญาตใน browser และเปิดผ่าน HTTPS. iPhone Safari อาจเปิดภาพกล้องได้ แต่ไม่มี FaceDetector API ในรุ่นนี้ จึงใช้ได้เฉพาะบันทึกรายการทดสอบ DEMO หลังเปิดกล้อง ไม่ได้ตรวจหรือระบุตัวตน

สลับบทบาทผ่านรายการด้านบน: Admin ใช้ PIN ทดลอง 1234 และ Admin ขั้นสูงใช้ 1994 ข้อมูลจะเก็บใน Local Storage ของเบราว์เซอร์และไม่ขึ้น Google Sheets การอนุมัติ/เพิ่มพนักงาน/ตั้งค่านโยบายจึงเป็นเพียงการสาธิต PIN นี้ฝังในโค้ดหน้าเว็บ ห้ามใช้กับข้อมูลจริง

## 2. สร้าง Google Sheets schema

1. สร้าง **Spreadsheet ใหม่** สำหรับ V2 beta; อย่าชี้ไปชีต V1 ที่มีข้อมูลจริง
2. เปิด **ส่วนขยาย → Apps Script** จาก Spreadsheet นั้น
3. ใช้ `Code.gs` ที่ระบบสร้างให้ แล้วเพิ่มไฟล์ `Setup.gs` และ `Reports.gs`
4. คัดลอกไฟล์ชื่อเดียวกันจาก `apps-script/` เข้า Apps Script แล้วกดบันทึก
5. เลือก `setupAll` แล้วกด **เรียกใช้** และอนุญาต Spreadsheet/Drive
6. ตรวจว่ามีชีต Employees, EmployeeTypes, UserAccounts, FaceTemplateIndex, Shifts, Worksites, AttendanceEvents, DailyAttendance, OTSegments, Approvals, HolidayCalendars, Holidays, Adjustments, AuditLog, Settings, BackupLog
7. เลือก `installTriggers` เพื่อสร้าง trigger สรุปวันก่อนหน้าช่วง 06:00 และตรวจ backup สิ้นเดือนช่วง 23:00 Asia/Bangkok

`setupAll()` สร้าง/ต่อหัวคอลัมน์โดยไม่ลบแถวข้อมูลเดิม แต่แนะนำให้ใช้ Spreadsheet ใหม่ใน V2 beta

### ขอบเขต API

`doGet` ตอบเฉพาะ health/ping; `doPost` ปฏิเสธการเขียนข้อมูล การทำเช่นนี้ตั้งใจป้องกันการเปิด public write endpoint ที่ยังไม่มี authentication, role check, signed face assertion และ replay protection อย่าเปิด API ให้ทุกคนหรือเปลี่ยน code ให้เขียนได้ก่อนติดตั้งระบบยืนยันตัวตนฝั่ง server

## 3. เปิด Python face-quality API ในเครื่อง

ใช้ Python 3.11 ในเครื่องทดลอง:

```sh
cd "ระบบ/เวอร์ชัน_2_เบต้า/face-api"
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FACE_API_TOKEN="ใส่ secret สุ่มยาวสำหรับเครื่องทดลอง"
export FACE_DETECTOR_MODEL_PATH="./models/face_detector.task"
uvicorn main:app --host 127.0.0.1 --port 8000
```

ต้องจัดหา MediaPipe task model ที่เลือกและตรวจเงื่อนไขใช้งานแล้วเอง; ไฟล์โมเดลไม่รวมใน repo/ZIP ฟังก์ชัน `/v1/face/quality` ตรวจจำนวน/ขนาด/ความคมของใบหน้าในหน่วยความจำและไม่บันทึกภาพ ส่วน `/v1/face/verify` ตอบ `501` โดยตั้งใจ จนกว่าจะเพิ่มโมเดล face recognition ที่ใช้เชิงพาณิชย์ได้, encrypted templates, PAD/liveness, calibration และ signed assertion

`FACE_API_TOKEN` และไฟล์โมเดลห้ามใส่ใน GitHub, Netlify `public/js/config.js` หรือ Apps Script frontend ส่วน service นี้ฟัง localhost เท่านั้นเป็นค่าเริ่มต้น ห้ามเปิดออกอินเทอร์เน็ตโดยไม่มี HTTPS, auth, rate limit และการตรวจความปลอดภัย

## 4. Deploy เว็บไป Netlify

- Base directory: `ระบบ/เวอร์ชัน_2_เบต้า`
- Build command: `npm run build`
- Publish directory: `dist`
- เชื่อม GitHub repo แล้ว deploy หลังตรวจ source

`public/js/config.js` ใส่ Apps Script URL ได้สำหรับกดตรวจ ping ในหน้าตั้งค่าเท่านั้น (ต้อง Deploy Web App และให้สิทธิ์เข้าถึงเหมาะสม); ping ไม่ได้เปิดอ่าน/เขียนข้อมูล. `faceApiUrl` คงว่างไว้จนกว่าจะมีบริการ face matching ที่ปลอดภัย

## ข้อจำกัดความปลอดภัยของ Demo roles

หน้าทดลองใช้รหัส Admin 1234 และ Admin ขั้นสูง 1994 เพื่อเปลี่ยนมุมมองเท่านั้น รหัสฝังใน JavaScript ที่ทุกคนเปิดดูได้ ไม่มีการยืนยันตัวตนฝั่ง server และห้ามใช้กับข้อมูลจริง/เปิดเป็นระบบพนักงานจริง

## ยังไม่ใช้งานจริง

- ไม่ได้จับคู่ว่าใบหน้าเป็นใคร; คะแนน 70% ไม่ได้เปิดใช้เป็น match score. บน Safari ปัจจุบัน fallback เป็น camera-only demo
- ไม่มี login/session จริง; PIN 1234/1994 เป็นเพียง gate ฝั่งหน้าเว็บ แก้ดูได้จาก source และไม่ปลอดภัย
- อนุมัติรายการในแอปแก้เฉพาะข้อมูลทดลองในเครื่อง
- Google Sheets API ยังปิด read/write; LINE summary ใน Apps Script เป็นข้อความ readiness ไม่ใช่สรุปเวลาเข้าออกจริง
- CSV เป็นตัวอย่างคอลัมน์ ยังไม่คำนวณสาย/OT และยังไม่เติม Excel แม่แบบรายคน
- ยังไม่ได้ติดตั้ง Python dependencies/model, สร้าง Drive/LINE จริง, deploy Netlify หรือทดสอบกล้องบน iPhone 13
- ก่อนเก็บใบหน้าพนักงานจริง ต้องผ่านการตรวจ PDPA/ความเป็นส่วนตัวและกำหนด consent/retention/fallback

## โครงสร้าง

- `src/` — React app และ responsive UI
- `apps-script/` — schema setup, API ปิด write, daily/backup triggers
- `face-api/` — Python quality-service scaffold; identity verification ปิดอยู่
- `SPEC.md` — ER/API/face scan spec จากดราฟ 4

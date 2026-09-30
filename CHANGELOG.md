# Changelog · NOVA Attendance V2 Beta

## 2.0.0-beta.1

- Created a separate mobile-first app folder from the Draft 4 design.
- Added the three bottom tabs, employee scan demo, personal history, employee admin form, advanced admin dashboard, shift/worksite settings, and annual holidays.
- Added Google Sheets schema setup, previous-day summary trigger, and month-end backup scaffold.
- Added Python face-quality API scaffold. Identity matching, face enrollment, PAD, login, and public data writes remain disabled.

## 2026-09-30 · Beta usability revision

- Added demo PIN prompts for Admin (1234) and Advanced Admin (1994); these are client-side demo gates, not real authentication.
- Made attendance rules and privacy options editable in Advanced Admin and clarified their local-only persistence.
- Fixed worksite save form to prevent navigation/reload and explicitly save local demo settings.
- Added Apps Script ping button; reports only endpoint readiness and does not enable data reads/writes.
- Camera-only fallback on iPhone Safari now allows clearly labeled local test events; it never represents face identification or a real attendance record.

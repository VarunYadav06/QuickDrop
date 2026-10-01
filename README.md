# ⚡ QuickDrop
A secure, self-destructing ephemeral file and text-sharing web application built with **FastAPI** and **Supabase**. Designed with a modern glassmorphic UI, real-time particle background physics, and instant QR code generation.

![QuickDrop Banner](https://img.shields.io/badge/Status-Live%20&%20Functional-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688)
![Supabase](https://img.shields.io/badge/Supabase-Cloud%20Storage-3FCF8E)

## ✨ Core Features
* **Dual Payload Support:** Securely upload files (up to 100MB) or paste code snippets/text directly.
* **Ephemeral Security:** Configurable expiration timers (default 1-hour lifespan).
* **Burn-on-Fetch Mechanics:** Payloads automatically self-destruct from both Supabase storage and the database once download limits or views are reached.
* **Instant QR Code Sharing:** Automatically generates a scan-to-receive QR code for seamless cross-device sharing.
* **Glassmorphic UI:** Built with smooth dynamic blur panels, cyber-pulse encryption overlays, and interactive particle animations.

## 🛠️️ Tech Stack
* **Backend:** FastAPI, Uvicorn, Python-Multipart, Pydantic
* **Database & Storage:** Supabase (PostgreSQL & Cloud Object Storage)
* **Frontend:** HTML5, Modern CSS (Glassmorphism), JavaScript (ES6+), Lucide Icons, QRCode.js

# 🩸 BloodLink

> Connecting donors, patients, and hospitals — faster than ever.

BloodLink is a blood donation management platform that bridges the gap between **blood donors**, **patients in need**, and **hospitals** — making the donation process faster, easier, and more accessible.

---

## 💡 The Problem

Finding the right blood donor at the right time is a critical challenge. BloodLink solves this by creating a smart, connected system where donors, patients, and hospitals can communicate and coordinate in real time.

---

## ✨ Features

- 🏥 **3 User Roles** — Donors, Patients, and Hospitals each have their own dashboard
- 📍 **Location-Based Filtering** — Find the nearest hospital or donor based on location
- 🔔 **Smart Alerts** — Notify donors when their blood type is needed nearby
- 📋 **Blood Request Management** — Hospitals can create and manage blood requests
- 🗃️ **Blood Inventory Tracking** — Hospitals track available blood units
- 📅 **Appointment Scheduling** — Book donation appointments directly through the platform
- 👤 **Donor & Patient Profiles** — Manage personal info, blood type, and donation history
- 📊 **Admin Reports** — Overview of donations, requests, and inventory

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python · Django |
| Frontend | HTML · CSS · JavaScript |
| Database | PostgreSQL · MySQL |
| Other | Django ORM · Django Auth |

---

## 🗂️ Project Structure

```
blood_donation/
│
├── accounts/        # User auth & registration (Donor, Patient, Hospital)
├── donors/          # Donor profiles, alerts & activity
├── hospitals/       # Hospital dashboard, inventory & blood requests
├── requests_app/    # Patient blood requests & alerts
├── core/            # Home & shared views
└── templates/       # All HTML templates
```

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/mriemmelbanna/BloodLink.git
cd BloodLink
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup the database
```bash
python manage.py migrate
```

### 4. Run the server
```bash
python manage.py runserver
```

Then open your browser at `http://127.0.0.1:8000` 🎉

---

## 👩‍💻 Developer

**Mariem Essam** — MIS Graduate | Full Stack Developer in Progress


<p align="center">Made with ❤️ to save lives 🩸</p>


# PMS 

A small open-source PMS app made with Django.


## Stored data
- Type of rooms: name, n° of guests and price per day
- Rooms: name, description
- Customers: name, email, phone
- Bookings: checkin, checkout, total guests, customer information, total amount


## Features
- Create, delete and check bookings for each room
- Check room availability
- Find bookings by code or customer name
- Dashboard with bookings, incoming and outcoming customers, total invoiced
- Get detailed information about each room
- Edit customer information

## Local Deployment

To deploy this project locally run


### Using Docker
```bash
    docker compose -f docker-compose.yml up
```

### Using Virtualenv

```bash
    pip install virtualenv
    virtualenv pms
    source pms/bin/activate
    pip install django
    git clone https://github.com/vsa-ok/chapp_pms
    cd chapp_pms
    pipenv sync
    python manage.py runserver
```

### Django admin (/admin)
Use for username and password for superuser is "admin" (without quotes).Remember to change it.

### Warnings
- SECRET_KEY should be stored in .env file for production!
- DEBUG is set to TRUE.

## TODO List / Improvements

- Handle and create error pages
- Validate dates for checkin/checkout in serverside
- Check for room availability exactly before save data in DB
- Change date or define date range in dashboard
- Improve and add more data in dashboard


## License
[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://choosealicense.com/licenses/mit/)


# Booking Engine Technical Test 🏨

**Candidate:** Benjamín Mehrez
**Role:** Senior Full Stack Developer
**Stack:** Python 3.10, Django, Docker, Bootstrap.

## 📋 Project Overview

This repository contains the solution for the Booking Engine technical assessment. The objective was to extend an existing Django legacy application with new features while strictly adhering to **Clean Code principles**, **robust testing**, and **business logic integrity**.

All changes were implemented using a **Feature Branch Workflow**, ensuring code isolation and modularity.

---

## 🚀 Implemented Features (Core Tasks)

### 1. Room Filtering
* **functionality:** Added a search bar to the "Rooms" list to filter by name.
* **Implementation:** Used case-insensitive lookups (`icontains`) and optimized the query using `.values()` to reduce database load.
* **UX:** Included a "Reset" button to clear filters easily.

### 2. Occupancy Rate Widget
* **Functionality:** Introduced a KPI widget in the Dashboard displaying the real-time Occupancy Rate.
* **Logic:** Calculated as `(Confirmed Bookings / Total Rooms) * 100`.
* **Reliability:** The calculation explicitly excludes cancelled bookings (`state='DEL'`) to ensure data accuracy.

### 3. Edit Booking Dates
* **Functionality:** Enabled modification of dates for active reservations.
* **Business Logic:**
    * **Price Recalculation:** Automatically updates the total price based on the new duration and room rate.
    * **Self-Correction:** Allows extending a booking even if it overlaps with its own previous dates (handling self-exclusion in queries).

---

## ✨ Enhancements & "Senior" Fixes

Beyond the requested tasks, several improvements were made to ensure the application is production-ready:

### 🛡️ Validations & Data Integrity
* **Concurrency Check (`is_taken`):** Implemented a "last-mile" availability check right before saving. This prevents double-booking race conditions if another user reserves the room while the first user is filling out the form.
* **Strict Date Validation:**
    * Check-in must be **today or in the future**.
    * Check-out must be **strictly after** check-in.
* **Phone Number Validation:** Added validation to prevent invalid data (e.g., single digits like "2").
* **Legacy Data Cleanup:** When editing an existing booking, the system now enforces contact info validation. Users cannot save date changes if their stored phone number is invalid; they are prompted to correct it.

### ⚙️ DevOps & Configuration
* **Modern Stack Compatibility:** Verified and validated application stability on **Python 3.10+** (tested via `python:latest` Docker image), ensuring the legacy codebase is compatible with modern runtime environments.
* **Docker Integration:** Validated the containerized environment to ensure seamless setup and execution of the test suite across different machines.
* **Environment Variables:** Prepared the project to read sensitive configurations via environment variables (where applicable).

### 🔔 UX/UI Improvements
* **Dynamic Alerts:** Integrated Django's `messages` framework to provide immediate feedback (Success/Error) for all actions (e.g., "Booking updated successfully", "No availability for selected dates").

---

## 🛠️ How to Run

The project is fully containerized.

1.  **Build and Start:**
    ```bash
    docker compose up --build
    ```
2.  **Access the Application:**
    Open your browser at `http://localhost:8000`

---

## ✅ Testing Strategy

A comprehensive test suite was written using `django.test.TestCase` to cover happy paths, edge cases, and business logic.

**Run All Tests:**
```bash
docker compose exec testservice python manage.py test pms


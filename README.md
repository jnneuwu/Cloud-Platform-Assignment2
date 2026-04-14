# Cloud Platform Assignment 2 Starter

This starter gives you a safe first step for the Dropbox-style assignment:

- FastAPI app entry point
- MongoDB connection and indexes
- first-login bootstrap logic for `User` and root `Directory`
- basic directory listing and create/delete directory UI
- a placeholder `firebase-login.js` file that must be replaced with the exact course example

## 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 2. Install dependencies

```powershell
pip install -r requirements.txt
```

## 3. Configure environment variables

Copy `.env.example` and set the values in your shell before starting the server.

Example in PowerShell:

```powershell
$env:MONGODB_URI = "your-mongodb-atlas-connection-string"
$env:MONGODB_DB_NAME = "cloud_platform_assignment"
$env:SESSION_SECRET = "replace-this"
$env:FIREBASE_PROJECT_ID = "your-firebase-project-id"
$env:FIREBASE_CREDENTIALS_PATH = "E:\path\to\firebase-service-account.json"
$env:AZURE_STORAGE_CONNECTION_STRING = "UseDevelopmentStorage=true"
$env:AZURE_CONTAINER_NAME = "dropbox-files"
```

## 4. Replace `static/js/firebase-login.js`

The assignment brief says the login system must match the course example exactly.
This starter includes only a placeholder file so the project structure is correct.
Before testing login, replace `static/js/firebase-login.js` with the exact file from your course example and make sure it posts the Firebase ID token to `/auth/login`.

## 5. Run the app

```powershell
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Current scope

This starter covers the first build stage only:

- app structure
- login integration point
- user bootstrap
- root directory creation
- create/delete directory basics

File upload/download, hashing, sharing, and Azurite integration should be added later.

# Mini Dropbox - CSP Assignment 2

A FastAPI implementation of a Dropbox-style cloud service. Authentication is
handled by Firebase, file metadata is stored in MongoDB Atlas, and file blobs
live in Azurite (locally) or Azure Blob Storage (deployed). The login flow
matches `PaaS-by-example.pdf` Example 03 exactly.

## Implemented features

- **Group 1**: login/logout via `static/firebase-login.js`; `users`,
  `directories`, `files` MongoDB collections; first-login bootstrap of the
  `User` document and root `/` directory; create / delete directory.
- **Group 2**: change directory; `../` go-up entry that hides at root; file
  upload to Azurite with overwrite confirmation.
- **Group 3**: delete file; download file; non-empty directory cannot be
  deleted; SHA-256 duplicate detection in the current directory (highlighted).
- **Group 4**: SHA-256 duplicate detection across the whole drive
  (`/duplicates`); read-only file sharing by email (`Shared with me` panel);
  clean responsive UI.

## 1. Create and activate a virtual environment

PowerShell:

```powershell
python -m venv env
./env/Scripts/Activate.ps1
```

Linux / macOS:

```bash
python3 -m venv env
source env/bin/activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

Only the libraries listed in the course example are used.

## 3. Set environment variables

| Variable | Purpose |
| --- | --- |
| `MONGODB_URI` | MongoDB Atlas connection string |
| `MONGODB_DB_NAME` | Database name (default `cloud_platform_assignment`) |
| `AZURE_STORAGE_CONNECTION_STRING` | `UseDevelopmentStorage=true` for Azurite |
| `AZURE_CONTAINER_NAME` | Blob container name (default `dropbox-files`) |

PowerShell example:

```powershell
$env:MONGODB_URI = "mongodb+srv://USER:PASSWORD@CLUSTER.mongodb.net/?retryWrites=true&w=majority"
$env:AZURE_STORAGE_CONNECTION_STRING = "UseDevelopmentStorage=true"
```

## 4. Add your Firebase config

Open `static/firebase-login.js` and replace the `firebaseConfig` object with
the snippet from your Firebase project (Project settings -> General -> Your
apps -> Use a `<script>` tag). **Do not modify any other part of that file.**

## 5. Start Azurite

In VS Code, install the *Azurite* extension and run
`Azurite: Start Blob Service` (Ctrl+Shift+P). It listens on
`127.0.0.1:10000` by default.

## 6. Run the app

```bash
uvicorn main:app --reload --port 8001
```

Open `http://127.0.0.1:8001`.

> Port 8001 (instead of FastAPI's default 8000) is used so the server does not
> clash with other local FastAPI projects you may be running on 8000.

## File layout

```
main.py                  # entire FastAPI server (single file, by-example style)
requirements.txt
README.md
.env.example
static/
  firebase-login.js      # course Example 03 script (only firebaseConfig changed)
  styles.css
templates/
  main.html              # login + drive view (single page)
  duplicates.html        # whole-drive duplicate detection view
```

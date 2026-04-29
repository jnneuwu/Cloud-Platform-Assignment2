# Mini Dropbox — Cloud Services & Platforms Assignment 2

A FastAPI implementation of a Dropbox-style cloud service. Authentication uses
Firebase, metadata lives in MongoDB Atlas, and file blobs are stored in Azurite
(local) or Azure Blob Storage (deployed). The login flow matches
`PaaS-by-example.pdf` Example 03 exactly: `static/firebase-login.js` puts the
Firebase ID token into a `token` cookie and the FastAPI server validates it
with `google.oauth2.id_token.verify_firebase_token`.

## 1. Create and activate a virtual environment

Windows (PowerShell):

```powershell
python -m venv env
./env/Scripts/activate.ps1
```

Windows (cmd):

```bat
python -m venv env
./env/Scripts/activate.bat
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

## 3. Configure environment variables

Copy `.env.example` and set the values in your shell before starting the server.
The required variables are:

| Variable | Purpose |
| --- | --- |
| `MONGODB_URI` | MongoDB Atlas connection string |
| `MONGODB_DB_NAME` | Database name to use (default `cloud_platform_assignment`) |
| `AZURE_STORAGE_CONNECTION_STRING` | `UseDevelopmentStorage=true` for Azurite, or the connection string from Azure Portal |
| `AZURE_CONTAINER_NAME` | Blob container name (default `dropbox-files`) |

PowerShell example:

```powershell
$env:MONGODB_URI = "mongodb+srv://USER:PASSWORD@CLUSTER.mongodb.net/?retryWrites=true&w=majority"
$env:AZURE_STORAGE_CONNECTION_STRING = "UseDevelopmentStorage=true"
```

## 4. Add your Firebase config

Open `static/firebase-login.js` and replace the `firebaseConfig` object with
the snippet from your Firebase project (Project settings → General → Your apps
→ Web app → Use a `<script>` tag). **Do not modify any other part of the
file** — the assignment brief requires `firebase-login.js` to match the
example exactly.

## 5. Start Azurite

In VS Code, install the *Azurite* extension and run `Azurite: Start Blob
Service` (Ctrl+Shift+P). It listens on `127.0.0.1:10000` by default.

## 6. Run the app

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Project layout

```
app/
  main.py                  # FastAPI entry point
  auth.py                  # google-auth Firebase token verifier
  config.py                # env-driven settings
  db.py                    # MongoDB client + indexes
  routes/web.py            # all HTTP routes
  services/
    bootstrap_service.py   # first-login user + root directory
    directory_service.py   # create / list / delete directories
static/
  firebase-login.js        # course Example 03 script (only firebaseConfig changed)
  styles.css
templates/
  main.html                # single-page UI (login box + drive view)
```

## Implemented (Group 1)

- Login / logout via Firebase exactly per the example
- `users`, `directories`, `files` MongoDB collections with unique indexes
- First-login bootstrap of the `User` document and root `/` directory
- Create directory in the current location (rejects duplicate names)
- Delete an empty directory (root cannot be deleted)

## Coming next

- Group 2: change directory, `../` navigation, file upload to Azurite with
  overwrite confirmation
- Group 3: file download / delete, prevent non-empty directory deletion,
  duplicate detection in current directory (SHA-256)
- Group 4: duplicate detection across the whole drive, read-only file sharing,
  polished UI

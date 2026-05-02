# Mini Dropbox - CSP Assignment 2

A FastAPI implementation of a Dropbox-style cloud service. Firebase handles
authentication, MongoDB Atlas stores file metadata, and Azurite (or real
Azure Blob Storage when deployed) holds the file blobs. The login flow
matches `PaaS-by-example.pdf` Example 03 exactly.

## How it fits together

```
browser ── token cookie ─▶ FastAPI (main.py) ── verify_firebase_token ─▶ Firebase
                                │
                                ├── metadata reads/writes ─▶ MongoDB Atlas
                                │     (users / directories / files)
                                │
                                └── file content reads/writes ─▶ Azurite
                                                                (blob container)
```

- The browser signs the user in with Firebase (in `firebase-login.js`) and
  stores the resulting ID token in a cookie called `token`.
- Every request to the FastAPI server reads that cookie and verifies it with
  `google.oauth2.id_token.verify_firebase_token`. No server-side session.
- Directory/file structure lives in MongoDB. Three collections:
  - `users` keyed by Firebase uid
  - `directories` with a `path` field (e.g. `/docs/photos`)
  - `files` with a `dir_id`, `sha256`, and `shared_with` list
- File bytes go to Azurite. The blob name is namespaced by uid + uuid so two
  users (or two uploads of the same name) never collide.

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
  responsive UI.

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
| `AZURE_STORAGE_CONNECTION_STRING` | Leave empty to use the built-in Azurite dev string |
| `AZURE_CONTAINER_NAME` | Blob container name (default `dropbox-files`) |

PowerShell example:

```powershell
$env:MONGODB_URI = "mongodb+srv://USER:PASSWORD@CLUSTER.mongodb.net/?retryWrites=true&w=majority"
```

These variables only live in the current PowerShell session - if you open a
new terminal you have to set them again (or put them in an `.env` and source
it).

## 4. Add your Firebase config

Open `static/firebase-login.js` and replace the `firebaseConfig` object with
the snippet from your Firebase project (Project settings -> General -> Your
apps -> Use a `<script>` tag). **Do not modify any other part of that file.**

In the Firebase console make sure you have:

- enabled the **Email/Password** sign-in provider under
  `Build -> Authentication -> Sign-in method`
- registered a **Web** app under `Project settings -> Your apps`

## 5. Start Azurite

In VS Code, install the *Azurite* extension and run
`Azurite: Start Blob Service` (Ctrl+Shift+P). It listens on
`127.0.0.1:10000` by default.

## 6. Run the app

```bash
uvicorn main:app --reload --port 8001
```

Open `http://127.0.0.1:8001`.

> Port 8001 (instead of FastAPI's default 8000) is used so the server does
> not clash with other local FastAPI projects.

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

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `uvicorn : not recognized` | Virtual environment not activated | Run `./env/Scripts/Activate.ps1` again - the prompt should show `(env)` |
| `ServerSelectionTimeoutError` from MongoDB | Atlas IP allowlist does not include your IP | In Atlas: `Network Access -> Add IP Address -> Allow Access from Anywhere` (`0.0.0.0/0`) |
| `bad auth: authentication failed` | Wrong password in `MONGODB_URI` | Re-copy the URI from Atlas and replace `<db_password>` with the user's actual password |
| `Connection string missing required connection details` | Old `UseDevelopmentStorage=true` shortcut | Leave `AZURE_STORAGE_CONNECTION_STRING` unset - the code now ships the full Azurite dev string as default |
| `EADDRINUSE: address already in use 127.0.0.1:10000` | Azurite is already running from a previous session | Ignore - Azurite is fine, the message just means another process already started the service |
| Browser shows `ERR_CONNECTION_REFUSED` on 8001 | Server crashed during startup or never started | Check the uvicorn terminal for a Python traceback |
| Login button does nothing | `firebaseConfig` in `static/firebase-login.js` is still the placeholder | Replace it with the real config from the Firebase console |
| `Token verification failed` printed in server log | Stale token cookie from another Firebase project | Click `Sign out`, then sign in again |

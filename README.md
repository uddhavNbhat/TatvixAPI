# 🚀 **Tatvix – Legal Assistant API**

Your personal AI-powered legal agent designed to help you understand the law in the simplest and most intuitive way.

This project is currently in **local development** and supports both **local LLMs** and **API-based cloud LLMs**, depending on your configuration.

---

# 🧱 **Prerequisites (Windows)**

Install these before running setup:

- **Python 3.10+**
- **Docker Desktop**
- **Docker Compose plugin**
- **MongoDB Community + MongoDB Compass**
- **SQLite (sqlite3 CLI available in PATH)**
- **Node.js 20+ (includes npm)**

### ✔ Quick verification

Run in PowerShell/CMD:

```bash
python --version
pip --version
docker --version
docker compose version
mongod --version
sqlite3 --version
node --version
npm --version
```

If any command fails, install that dependency and ensure it is added to **PATH**.

---

# 📦 **Setup & Installation**

## 1. **Clone the Repository**

```bash
git clone <public_repo_link>
```

> _(Repository not public yet)_

---

# ⚙️ **Environment Setup**

Create a `.env` file in the root directory with the following variables:

```env
SQLITE_DB_NAME="TatvixDB.db"
JWT_SECRET_KEY="your_secret_key_here"
ENC_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALLOWED_ORIGIN="http://localhost:5173"
MONGODB_URI="mongodb://localhost:27017/TatvixDb"
WEAVIATE_SERVER="http://localhost:8081/vectors"
GOOGLE_API_KEY="your_google_api_key_here"
MCP_SERVER="http://localhost:5050/mcp"
```

### **Important Notes**

- Generate a strong JWT secret via: [https://jwtsecrets.com](https://jwtsecrets.com)
- Google API key → create in **Google AI Studio**
- Supported LLMs → **Gemini 2.5 Flash / Pro**
- Uses:
  - SQLite (local user/session storage)
  - MongoDB (document store)
  - Weaviate (vector DB)
  - Local inference server (Gemma 300M embeddings)

---

# ⚙️ **Guided Setup (One by One)**

From project root, run:

```bash
setup.bat
```

The script first shows prerequisite checks, then asks:

`Type YES to begin setup`

Only after you type **YES**, it runs these steps in order:

1. Build Docker image for `file_service_API`
2. Build Docker image(s) for `Gemma_Inference_API`
3. Install Python requirements in `TatvIX_API`
4. Install npm packages in `TatvixFrontend`

If any step fails, setup stops with a clear error message so you can fix and rerun.

---

# 🗃️ **Setup Server — Document Ingestion Layer**

The setup server handles:

✔ Document upload
✔ MongoDB storage
✔ Chunking & embedding generation
✔ Pushing embeddings into Weaviate

### ⚠️ _Note:_

Avoid huge files unless your system has enough RAM to perform embedding inference.

---

# 🔌 **Setup API – Endpoints**

Use **Postman** to interact with ingestion endpoints.

---

## **1. Upload Documents → MongoDB**

```
POST http://localhost:5000/populate-mongodb
```

**Body → form-data**

- `file`: list of files (PDF/text documents)

---

## **2. Populate Vector DB (Weaviate)**

```
POST http://localhost:5000/populate-weaviate
```

No body required.
Uses documents already stored in MongoDB.

---

## **3. Drop Weaviate Database**

```
POST http://localhost:5000/drop-weaviate-db
```

⚠️ **Warning:** Deletes all embeddings & vectors.

---

# 🧠 **Application Server (Main API)**

This server handles:

- Authentication
- Chat sessions
- Legal agent responses
- Retrieval-augmented generation
- MCP-based document search

To explore the APIs interactively:

```
http://localhost:8000/docs
```

Powered by **FastAPI Swagger UI**.

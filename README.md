
# 🚀 **Tatvix – Legal Assistant API**

Your personal AI-powered legal agent designed to help you understand the law in the simplest and most intuitive way.

This project is currently in **local development** and runs entirely on your machine.

---

# 📦 **Setup & Installation**

## 1. **Clone the Repository**

```bash
git clone <public_repo_link>
```

> *(Repository not public yet)*

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

* Generate a strong JWT secret via: [https://jwtsecrets.com](https://jwtsecrets.com)
* Google API key → create in **Google AI Studio**
* Supported LLMs → **Gemini 2.5 Flash / Pro**
* Uses:

  * SQLite (local user/session storage)
  * MongoDB (document store)
  * Weaviate (vector DB)
  * Local inference server (Gemma 300M embeddings)

---

# 🐳 **Docker & Model Setup**

Before running the system:

## 1. **Start Docker Desktop**

Weaviate and the embedding inference container require Docker to be running.

---

## 2. **Install the Embedding Model (Gemma 300M)**

Tatvix uses **Gemma 300M Embedding Model**, optimized for edge devices.

Inside the folder:

```
TatvIX_API/Transformer_Inference_API/
```

Run this Python snippet to download the model:

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="google/embeddinggemma-300M",
    local_dir="./models/gemma-300m",
    local_dir_use_symlinks=False
)
```

Your final directory structure must look like:

```
TatvIX_API/
└── Transformer_Inference_API/
    └── models/
        └── gemma-300m/   <-- model files here
```

This folder is mounted by the inference Docker container at runtime.

---

## 3. **Run the Setup Script**

After Docker is running and the model is installed:

```bash
C:\<path_to_project>\TatvIX_API\setup.bat
```

Follow the on-screen instructions.

---

# 🗃️ **Setup Server — Document Ingestion Layer**

The setup server handles:

✔ Document upload
✔ MongoDB storage
✔ Chunking & embedding generation
✔ Pushing embeddings into Weaviate

### ⚠️ *Note:*

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

* `file`: list of files (PDF/text documents)

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

* Authentication
* Chat sessions
* Legal agent responses
* Retrieval-augmented generation
* MCP-based document search

To explore the APIs interactively:

```
http://localhost:8000/docs
```

Powered by **FastAPI Swagger UI**.


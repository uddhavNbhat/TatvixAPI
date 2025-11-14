# **Tatvix – Legal Assistant API**

Your personal AI-powered legal agent that helps you understand law in the simplest way possible.

This project is currently in the **local development phase**, and you can run it entirely on your system.

---

## **Getting Started**

### **1. Clone the Repository**

Clone the project to your local machine:

```bash
git clone <public_repo_link>
```

(Not yet public)

---

## 🔧 **Environment Setup**

Before running the application, you must create a `.env` file in the project root with the following environment variables:

```env
SQLITE_DB_NAME="TatvixDB.db"
JWT_SECRET_KEY="your_secret_key_here"  # Generate from https://jwtsecrets.com
ENC_ALGORITHM="HS256"  # Use RS256 in production (asymmetric key-pair signing)
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALLOWED_ORIGIN="http://localhost:5173"
MONGODB_URI="mongodb://localhost:27017/TatvixDb"
WEAVIATE_SERVER="http://localhost:8081/vectors"
GOOGLE_API_KEY="your_google_api_key_here"
MCP_SERVER="http://localhost:5050/mcp"
```

### Notes:

* Generate a secure JWT secret key using **jwtsecrets.com**.
* Retrieve a Google API key from **Google AI Studio**.
* The LLM support currently uses **Gemini 2.5 Flash / Pro**.

---

## **Running the System**

After creating your .env file, ensure the following steps are completed before starting the system.

1. Start Docker Desktop (Windows)

The setup requires Docker to run the Weaviate + Transformer inference containers.

2. Install the Embedding Model Locally

The embedding model is not bundled with the repository and must be downloaded manually.

Tatvix uses the Gemma 300M Embedding Model (Edge device model) for generating vector embeddings.

Download & Place the Model
Run the below piece of code in python REPL/ or a simple script file to download gemma 300m into the system.
Make sure you run it inside the Gemma_Inference_API folder.

```
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="google/embeddinggemma-300M",
    local_dir="./models/gemma-300m",
    local_dir_use_symlinks=False
)

```

Download the Gemma 300M Embedding Model from the official Google/Model provider source.

Create the following directory (if it doesn’t already exist):

TatvIX_API/
└── Transformer_Inference_API/
    └── models/


Place the downloaded model inside the models folder.

The expected path becomes:

Transformer_Inference_API/models/<gemma-300m-model-files-here>


This folder is mounted by the inference Docker container during startup, ensuring the embedding service works correctly.

3. Run the Setup Script

Once Docker Desktop is running and the model is installed:

C:\<path_to_project>\TatvIX_API\setup.bat


Follow the on-screen instructions provided by the script.

---

## **Setup Server (Document Ingestion Layer)**

The **setup server** does not include a UI.
You can upload documents (PDFs, text files, etc.) to prepare the system. It handles:

* Spinning up a Weaviate database
* Storing uploaded documents in MongoDB
* Generating embeddings
* Populating the vector database with embeddings

> **Note:** Avoid extremely large documents as embedding generation depends heavily on your system resources.

---

## **Setup API Endpoints**

Use **Postman** to interact with these endpoints.

### **1. Upload Documents to MongoDB**

```
POST http://localhost:5000/populate-mongodb
Body → form-data:
file → (list of files)
```

### **2. Populate Weaviate with Embeddings**

```
POST http://localhost:5000/populate-weaviate
Body → none (uses documents already stored in MongoDB)
```

### **3. Drop Weaviate Database**

```
POST http://localhost:5000/drop-weaviate-db
```

⚠️ *Use with caution — this resets your vector database.*

---

## **Application Server (Main API)**

The application server exposes user-facing endpoints.

A UI is under development, but you can test APIs using **Postman**.

To explore the full API documentation, use FastAPI's built-in Swagger UI:

```
http://localhost:8000/docs
```

---

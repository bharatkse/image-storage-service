# Image Storage – Local Development Guide

A **serverless Image Storage service** built with **AWS SAM, LocalStack, Docker, Poetry, and OpenAPI**.

This repository demonstrates how to design, build, and run a **cloud-native backend locally** while keeping workflows deterministic, testable, and close to real AWS.

The **Makefile is the single entry point** for setup, development, testing, and deployment.

---

## ✨ Goals of This Setup

* Mimic AWS infrastructure locally using **LocalStack**
* Keep workflows **CI-friendly and reproducible**
* Enforce **clean architecture, linting, typing, and tests**
* Make onboarding trivial (**one-command setup**)

---

## 🧱 Tech Stack

* **Python 3.10**
* **AWS SAM** – Lambda packaging & Infrastructure as Code
* **LocalStack** – Local AWS services (S3, DynamoDB, Lambda, API Gateway)
* **Poetry** – Dependency & virtualenv management
* **Docker / Docker Compose** – Infrastructure orchestration
* **OpenAPI 3.0** – API contract
* **pre-commit, ruff, mypy, pytest** – Quality gates

---

## 📁 Project Structure (Relevant)

```text
.
├── infra/
│   └── template.yaml        # SAM / CloudFormation template
├── openapi/
│   └── api.yaml             # OpenAPI specification
├── src/                     # Lambda source code
├── seed/                    # Local data seeding utilities
│   ├── seed_images.py       # Seed data via API Gateway
│   ├── data/
│   │   └── images.json      # Sample image metadata
│   └── images/              # Sample image files
├── scripts/
│   └── bootstrap.sh         # Environment bootstrap
├── docker-compose.yml       # LocalStack + Swagger UI
├── Makefile                 # Primary developer interface
└── README.md

```

---

## 🚀 Setup & First Run (Start Here)

### 1️⃣ One-Command Local Setup

```bash
make bootstrap
make cf-deploy
```

This performs a **full local environment setup**:

1. Starts Docker and LocalStack
2. Installs Python dependencies via Poetry
3. Validates the OpenAPI specification
4. Uploads OpenAPI to LocalStack S3
5. Builds the SAM application
6. Deploys the CloudFormation stack to LocalStack

---

### 2️⃣ Verify Services Are Running

| Service           | URL                                                                                  |
| ----------------- | ------------------------------------------------------------------------------------ |
| LocalStack Health | [http://localhost:4566/_localstack/health](http://localhost:4566/_localstack/health) |
| Swagger UI        | [http://localhost:8080](http://localhost:8080)                                       |

Check LocalStack health explicitly:

```bash
curl http://localhost:4566/_localstack/health | jq
```

You should see `s3`, `dynamodb`, `lambda`, and `apigateway` marked as **running**.

---

## 🔑 Discover API Gateway & API Key (Single Command)

Retrieve **both the API Gateway ID and API Key** using one command.

```bash
make ls-api
```

Example output:

```text
-----------------------------------------
|              GetRestApis              |
+------------------------+--------------+
|  image-storage-api-snd |  nsxw5bxa8j  |
+------------------------+--------------+
+-------------------------------------------------------------------+
|                       GetApiKey                                    |
+------------------------+------------------------------------------+
|  image-storage-api-snd |  TwgChRfGmLc2bWNFKaiZ4M6rUlSzYJ1nO3svXQBk |
+------------------------+------------------------------------------+
```

### What to copy

* **API Gateway ID** → `nsxw5bxa8j`
* **API Key** → `TwgChRfGmLc2bWNFKaiZ4M6rUlSzYJ1nO3svXQBk`

### API base URL

```text
http://localhost:4566/restapis/<API_ID>/snd/_user_request_/v1
```

---

## 🔌 Test the APIs (End-to-End)

The following examples demonstrate the **complete lifecycle** of an image:

**upload → list → download → delete**

---

### 1️⃣ Upload an Image

Uploads a Base64‑encoded image to S3 and stores metadata in DynamoDB.

```bash
curl -X POST \
  http://localhost:4566/restapis/<API_ID>/snd/_user_request_/v1/images \
  -H "Content-Type: application/json" \
  -H "x-api-key: <API_KEY>" \
  -d '{
    "user_id": "user123",
    "image_name": "vacation-photo.jpg",
    "description": "Summer vacation at the beach",
    "tags": ["vacation", "beach"],
    "file": "<BASE64_ENCODED_IMAGE>"
  }'
```

**Expected result**
- HTTP **201 Created**
- Response contains a generated `image_id`

Save the returned `image_id` for the next steps.

---

### 2️⃣ List Images for a User

Retrieves all images belonging to a user, including metadata.

```bash
curl -X GET \
  "http://localhost:4566/restapis/<API_ID>/snd/_user_request_/v1/images?user_id=user123" \
  -H "x-api-key: <API_KEY>"
```

**Expected result**
- HTTP **200 OK**
- JSON response with an array of image metadata

---

### 3️⃣ Get / Download an Image

Retrieves an image from S3 via API Gateway. This endpoint supports **both inline viewing and forced download**, and can optionally include metadata in response headers.

**Query parameters**:

* `metadata=true` → includes image metadata in the `X-Image-Metadata` response header
* `download=true` → forces file download using `Content-Disposition: attachment`

```bash
curl -X GET \
  "http://localhost:4566/restapis/<API_ID>/snd/_user_request_/v1/images/<IMAGE_ID>" \
  -H "x-api-key: <API_KEY>" \
  --output downloaded-image.jpg
```

#### ▶️ View Image Inline (default behavior)

Displays the image inline (e.g., in browser or curl output) without forcing download.

```bash
curl -X GET \
  "http://localhost:4566/restapis/<API_ID>/snd/_user_request_/v1/images/<IMAGE_ID>" \
  -H "x-api-key: <API_KEY>"
```

#### ⬇️ Force Download

Forces the image to download by setting `Content-Disposition: attachment`.

```bash
curl -X GET \
  "http://localhost:4566/restapis/<API_ID>/snd/_user_request_/v1/images/<IMAGE_ID>?download=true" \
  -H "x-api-key: <API_KEY>" \
  --output downloaded-image.jpg
```

**Expected result**

- HTTP **200 OK**
- Image saved locally as `downloaded-image.jpg`

### 4️⃣ Delete an Image

Deletes the image from S3 and removes its metadata from DynamoDB.

```bash
curl -X DELETE \
  "http://localhost:4566/restapis/<API_ID>/snd/_user_request_/v1/images/<IMAGE_ID>" \
  -H "x-api-key: <API_KEY>"
```

**Expected result**
- HTTP **200 OK**
- Confirmation message indicating successful deletion

---
### 5️⃣ Troubleshooting Errors

Check logs:

```bash
make docker-logs
```

Restart Hard if needed:

```bash
make restart-hard
```

---
## 🌱 Seed Sample Data (Via API)
Seeding uses **real API Gateway endpoints**, not Lambda shortcuts.

```curl
poetry run python seed/seed_images.py \
  --api-id <API_ID> \
  --api-key <API_KEY>

```
This validates the **entire request path:**

**API Gateway → Lambda → S3 → DynamoDB**

---
## 🔍 Inspect LocalStack Resources
### 📦 DynamoDB
| Command              | Description                  |
| -------------------- | ---------------------------- |
| `make ls-dynamodb`   | List DynamoDB tables         |
| `make scan-dynamodb` | Scan and display table items |

```bash
make scan-dynamodb
```
OR
```bash
make scan-dynamodb DYNAMODB_TABLE=my-table-name
```

### 🪣 S3 (Uploaded Files)
| Command              | Description              |
| -------------------- | ------------------------ |
| `make ls-s3`         | List S3 buckets          |
| `make ls-s3-objects` | List uploaded S3 objects |

```bash
make ls-s3-objects
```
OR
```bash
make ls-s3-objects S3_BUCKET=my-bucket-name
```

This confirms that **actual image files were uploaded.**


⬇️ **Everything below this point explains the tools and workflows in detail.**

---

## 🧭 Makefile Philosophy

The Makefile is designed to:

* Expose **intent-based commands** (not low-level AWS calls)
* Hide LocalStack quirks behind sane defaults
* Work both locally and in CI without changes

> If you understand the Makefile, you understand the project.

---

## 🆘 Help

```bash
make help
```

Lists all available commands grouped by concern.

---

## 🐍 Poetry – Dependency Management

| Command                  | Description              |
| ------------------------ | ------------------------ |
| `make poetry-install`    | Install dependencies     |
| `make poetry-update`     | Update dependencies      |
| `make poetry-lock`       | Generate lock file       |
| `make poetry-check`      | Validate pyproject.toml  |
| `make poetry-show`       | Show dependency tree     |
| `make poetry-shell`      | Activate virtualenv      |
| `make poetry-export`     | Export prod requirements |
| `make poetry-export-dev` | Export dev requirements  |

---

## 🧪 Code Quality & Testing

| Command           | Description              |
| ----------------- | ------------------------ |
| `make lint`       | Run all pre-commit hooks |
| `make format`     | Auto-format code (ruff)  |
| `make type-check` | Run mypy                 |
| `make test`       | Run test suite           |
| `make coverage`   | Run tests with coverage  |
| `make clean`      | Remove build artifacts   |

Run a single test:

```bash
make test TEST=tests/handlers/test_upload.py
```

---

## 🐳 Docker & LocalStack

| Command               | Description            |
| --------------------- | ---------------------- |
| `make docker-up`      | Start LocalStack       |
| `make docker-down`    | Stop containers        |
| `make docker-restart` | Restart LocalStack     |
| `make docker-status`  | Show LocalStack status |
| `make docker-health`  | Check health endpoint  |
| `make docker-logs`    | Follow logs            |
| `make docker-shell`   | Shell into container   |
| `make docker-clean`   | Prune Docker resources |

---

## ☁️ CloudFormation / SAM

| Command          | Description                |
| ---------------- | -------------------------- |
| `make cf-build`  | Build SAM application      |
| `make cf-deploy` | Deploy stack to LocalStack |
| `make cf-status` | Show stack status          |
| `make cf-logs`   | Show recent stack events   |
| `make cf-delete` | Delete stack & cleanup     |

Deployment uses:

* `CAPABILITY_NAMED_IAM`
* `CAPABILITY_AUTO_EXPAND`
* No interactive prompts

---

## 🔍 Inspect LocalStack Resources

| Command              | Description           |
| -------------------- | --------------------- |
| `make ls-s3`         | List S3 buckets       |
| `make ls-dynamodb`   | List DynamoDB tables  |
| `make ls-lambda`     | List Lambda functions |
| `make ls-apigateway` | List API Gateways     |
| `make ls-resources`  | List all above        |

---


## 💻 Maintainer

**Bharat Kumar**  </br>
_Senior Software Engineer | Cloud & Backend Systems_  </br>
📧 kumar.bhart28@gmail.com </br>
🔗 [LinkedIn](https://www.linkedin.com/in/bharat-kumar28)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

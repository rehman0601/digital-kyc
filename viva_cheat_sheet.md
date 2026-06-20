# Digital KYC DevOps Platform - Viva Preparation Cheat Sheet

This document compiles the end-to-end architectures, tool mappings, command references, and essential viva Q&As for your B.Tech Computer Science / DevOps project.

---

## 1. Project Overview & Architecture

### The Core Problem Statement
fintech organizations onboarding new customers manually suffer from slow processing times, document security risks, lack of audit trails, and human errors. 
This project implements a **Digital KYC Verification Platform** — a Python/Flask web app combined with a modern cloud-native DevOps stack (AWS, EKS, RDS, S3, Docker, Kubernetes, Jenkins, Terraform) to build a secure, automated, scalable, and self-healing onboarding platform.

### DevOps Architecture Pipeline Flow
```
Developer writes code 
   ↓
Pushes to GitHub Repository
   ↓ (Webhook / Poll triggers)
Jenkins CI/CD Pipeline (Builds virtualenv → Smoke tests app → Builds Docker image → Deploys to Kubernetes)
   ↓
Kubernetes Cluster (Orchestrates containers: 2 Flask App replicas + Autoscaling HPA + MySQL database)
   ↓
AWS Infrastructure (EKS for K8s orchestration, RDS for MySQL, S3 for KYC document storage, CloudWatch for logs)
   ↓
Prometheus & Grafana (Scrapes metrics and displays application resource usage & request health)
```

---

## 2. Technology Stack Mapping

| Component / Layer | Technology | Specific Role in this Project |
| :--- | :--- | :--- |
| **Backend Framework** | Python / Flask | Runs the user registration, login, document upload portal, and admin approval views. |
| **Relational Database**| MySQL (via RDS) | Stores hashed user credentials, document paths, and verification statuses. |
| **Cloud Computing** | AWS EKS | Managed Kubernetes service hosting the Flask application pods in a high-availability design. |
| **Cloud Database** | AWS RDS | Managed MySQL database hosting the user/document databases with automatic backups. |
| **Cloud Storage** | AWS S3 | Secure, versioned bucket for raw KYC files (Aadhaar/PAN/Passport) with public access blocked. |
| **Infrastructure (IaC)**| Terraform | Defines and provisions the EKS cluster, node groups, RDS, S3, and IAM roles as configuration files. |
| **Containerization** | Docker | Packages the Flask app, dependencies, and WSGI server (`gunicorn`) into a lightweight container image. |
| **CI/CD Orchestration**| Jenkins | Runs declarative pipeline stages (Build, Test, Image Build, Deploy) on every code push. |
| **Autoscaling** | Kubernetes HPA | Scales Flask pods automatically from 2 up to 10 instances when CPU usage exceeds 70%. |
| **Observability** | Prometheus & Grafana| Collects container request counts, latencies, and CPU/RAM usage; visualizes them on graphical dashboards. |
| **Secure Management** | HashiCorp Vault | Encrypts database passwords, secret keys, and AWS access credentials to prevent exposure in code. |

---

## 3. DevOps Commands Cheat Sheet

### Git & GitHub Workflow
* `git init` – Initializes the local Git repository.
* `git status` – Shows modified files, untracked directories, and current branch state.
* `git log --oneline` – Prints a condensed history of commits (e.g. `450bda2 Initial commit of Digital KYC DevOps platform`).
* `git checkout -b main` – Creates and switches to the main branch.

### Local Application Execution (Development)
* `python3 -m venv venv` – Creates a Python virtual environment.
* `source venv/bin/activate` – Activates the virtual environment.
* `pip install -r requirements.txt` – Installs all packages.
* `PORT=5001 python app.py` – Boots the Flask app locally on port 5001 (defaulting to SQLite backend).

### Containerization (Docker & Colima)
* `colima start` – Starts the lightweight Linux container VM daemon on macOS.
* `docker build -t digital-kyc:latest .` – Builds the container image from the `Dockerfile`.
* `docker run -p 5002:5000 --name digital-kyc-container -d digital-kyc:latest` – Runs the container in detached mode (`-d`) mapping host port 5002 to container port 5000.
* `docker ps` – Lists all active container runtimes.
* `docker logs digital-kyc-container` – Displays stdout logs of the Flask app and Gunicorn server.
* `colima stop` – Shuts down the container VM to save battery/RAM.

### Kubernetes Deployment (kubectl)
* `kubectl apply -f k8s/database.yaml` – Deploys database secrets, PV storage, MySQL database pod, and internal database service.
* `kubectl apply -f k8s/deployment.yaml` – Deploys the 2-replica Flask web application pods and the HorizontalPodAutoscaler (HPA).
* `kubectl apply -f k8s/service.yaml` – Exposes the Flask app to external users using a NodePort (port 30050).
* `kubectl get pods` – Fetches status of all active database and application pods.
* `kubectl get svc` – Lists K8s services to see IP mappings and ports.

### Infrastructure Provisioning (Terraform)
* `terraform init` – Downloads the AWS provider plug-ins.
* `terraform plan` – Previews the 24 AWS resources (VPC, subnets, EKS, RDS, S3, IAM) to be created.
* `terraform apply` – Deploys the infrastructure directly to AWS.
* `terraform destroy` – Deletes all AWS infrastructure to avoid billing.

---

## 4. Top 15 Viva Questions & Answers

#### **Q1: What is the purpose of Gunicorn in your Dockerfile?**
> **A:** Gunicorn (Green Unicorn) is a production-ready Python WSGI HTTP server. Flask's built-in server is a development server that only handles one request at a time. Gunicorn uses a pre-fork worker model (we set `--workers 2`) to process concurrent requests in parallel, preventing delays in high-traffic production environments.

#### **Q2: Why did we consolidate the Kubernetes manifests into `database.yaml`?**
> **A:** We grouped database-related assets (Secrets, PersistentVolumes, PersistentVolumeClaims, MySQL Deployments, and MySQL Services) into a single, cohesive file because they represent the database dependency layer. Applying `database.yaml` first ensures all configuration, credentials, and storage are in place before the application deployment tries to connect.

#### **Q3: What is the difference between a PersistentVolume (PV) and a PersistentVolumeClaim (PVC)?**
> **A:** A **PV** is the actual physical storage provisioned by the cluster administrator (like a piece of a hard drive). A **PVC** is a request for that storage by a developer or pod. In Kubernetes, the MySQL pod claims 1Gi of storage through the PVC, ensuring database records survive if the MySQL container crashes or restarts.

#### **Q4: How did you implement High Availability (HA) in Kubernetes?**
> **A:** High availability was achieved in two ways:
> 1. By setting `replicas: 2` in [k8s/deployment.yaml](file:///Users/rehman/Downloads/files/digital-kyc/k8s/deployment.yaml), meaning K8s runs two identical copies of the Flask application across different nodes. If one fails, traffic is immediately sent to the other.
> 2. By defining a **HorizontalPodAutoscaler (HPA)** that dynamically increases replicas up to 10 if CPU load exceeds 70%.

#### **Q5: What is the significance of the `/health` and `/metrics` routes in `app.py`?**
> **A:** 
> * `/health` is used by **Kubernetes Liveness & Readiness Probes** to check if the app is healthy. If a container returns a non-200 status code, Kubernetes automatically restarts it.
> * `/metrics` is a Prometheus scraping endpoint. It exposes application-specific performance data (request counts, latency averages) that Prometheus gathers to build Grafana dashboards.

#### **Q6: How did you integrate AWS Rekognition (OCR) into the application?**
> **A:** In [app.py](file:///Users/rehman/Downloads/files/digital-kyc/app.py), we added a helper function `perform_aws_ocr_and_rekognition` that triggers when a customer uploads Aadhaar, PAN, or Passport files. It uses `boto3` (AWS SDK) to call AWS Rekognition/Textract to extract text and analyze faces. It falls back to a simulated OCR output locally, logging the steps and storing the analysis directly in the database `remarks` field.

#### **Q7: What does `terraform init` do under the hood?**
> **A:** It scans the Terraform configuration files, reads the required provider block (here `hashicorp/aws`), downloads the necessary binary plugins to communicate with the AWS API, and creates a `.terraform` lock file.

#### **Q8: What is the Terraform State File (`terraform.tfstate`)?**
> **A:** It is a JSON file where Terraform maps your real-world AWS infrastructure back to your code. It tracks resource metadata, IDs, and configurations so Terraform knows what to modify or delete next time you run `terraform apply` or `terraform destroy`.

#### **Q9: Why are EKS worker nodes deployed in multiple subnets/availability zones?**
> **A:** To prevent single-point-of-failure (SPOF) outages. EKS requires subnets in at least two different Availability Zones (like `ap-south-1a` and `ap-south-1b`). If an entire AWS data center goes offline, your worker nodes in the other zone continue running the platform.

#### **Q10: Why did we define security groups for AWS RDS?**
> **A:** To enforce **least privilege access control**. The RDS MySQL database security group is configured to allow inbound traffic *only* on port 3306 from the VPC CIDR block where the EKS nodes run. This prevents public internet hackers from directly accessing the database.

#### **Q11: What is a Declarative Jenkins Pipeline?**
> **A:** It is a modern Jenkinsfile format structured in a block hierarchy (using `pipeline {}`, `stages {}`, `steps {}`). It defines the pipeline structure as code, which can be checked into version control (git), rather than clicking buttons to build jobs inside the Jenkins GUI.

#### **Q12: How does the Jenkinsfile handle testing when pytest code is deleted?**
> **A:** We replaced the complex `pytest` framework tests with an import smoke test: `python -c "import app"`. This simple test ensures that the application script, SQL schemas, and python dependencies build and import without syntax errors. If this import fails, the pipeline fails early, blocking bad code from deploying.

#### **Q13: How does the application connect to different databases locally vs. in K8s?**
> **A:** We use **Environment Variables**. In [app.py](file:///Users/rehman/Downloads/files/digital-kyc/app.py), the code checks for `DATABASE_URL` or `DB_HOST`. If it finds nothing (like when running on a laptop), it falls back to a local `sqlite:///kyc.db` file. If running in K8s, the deployment manifest injects the MySQL database connection values (fetched from K8s secrets), allowing portability without editing the source code.

#### **Q14: Explain the difference between Base64 and Encryption in Kubernetes Secrets.**
> **A:** Base64 is **encoding**, not encryption. It is used to format binary data as text (e.g. `kyc_user` encodes to `a3ljX3VzZXI=`). Anyone can decode it instantly (`echo a3ljX3VzZXI= | base64 -d`). True encryption scrambles the data using a key, making it unreadable without the decryption password. For real encryption, we use HashiCorp Vault.

#### **Q15: What is the Disaster Recovery (DR) plan for the system?**
> **A:** Our DR plan relies on backups of three main areas:
> 1. **Codebase**: Pushed and backed up in the Git repository history.
> 2. **Data**: Running `mysqldump` commands to backup the MySQL DB to `.sql` files, along with archiving the `uploads/` directory.
> 3. **Infrastructure**: Provisioned dynamically by running `terraform apply` to recreate the entire VPC, database, storage buckets, and server nodes from scratch if AWS regions go down.

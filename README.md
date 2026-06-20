# Digital KYC Verification Platform

A Customer KYC Verification web app (Flask + MySQL/SQLite) built to
demonstrate a full DevOps lifecycle: GitHub -> Docker -> Jenkins ->
Kubernetes -> Terraform -> AWS -> Monitoring -> Logging -> Security ->
Disaster Recovery.

## What it does

- Users register, log in, upload KYC documents (Aadhaar / PAN / Passport),
  and track their verification status (Pending / Approved / Rejected).
- Admins see a dashboard of all submissions and can approve/reject with remarks.

## Project Structure

```
digital-kyc/
├── app.py                  # Flask application (Phase 1)
├── requirements.txt
├── tests/test_app.py       # Basic test suite (used by Jenkins)
├── templates/, static/     # UI
├── Dockerfile               # Phase 3
├── docker-compose.yml       # Run Flask + MySQL locally with one command
├── Jenkinsfile               # Phase 4
├── k8s/                      # Phase 5 - deployment, service, mysql, PV, secrets
├── terraform/                 # Phase 6 - EC2, Security Group, S3
├── monitoring/                 # Phase 8 - Prometheus + Grafana
├── logging/                     # Phase 9 - Logstash/ELK config
├── security/vault-notes.md       # Phase 10 - Vault architecture
└── disaster-recovery/             # Phase 11 - backup.sh / restore.sh
```

## Running it yourself

### Option A: Plain Python (fastest way to demo the app itself)

```bash
python3 -m venv venv
source venv/bin/activate          # venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
```

Visit http://127.0.0.1:5000 — default admin login is `admin` / `admin123`
(uses SQLite automatically, no DB setup needed).

### Option B: Docker (single container)

```bash
docker build -t digital-kyc:latest .
docker run -p 5000:5000 digital-kyc:latest
```

### Option C: Docker Compose (Flask + MySQL — closest to the real architecture)

```bash
docker compose up --build
```

### Option D: Kubernetes (minikube)

```bash
minikube start
eval $(minikube docker-env)        # so minikube can see your local image
docker build -t digital-kyc:latest .

kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/persistent-volume.yaml
kubectl apply -f k8s/mysql.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

kubectl get pods
kubectl get services
minikube service kyc-flask-service --url
```

### Option E: Terraform (provisions real AWS infra — costs apply)

```bash
cd terraform
terraform init
terraform plan
terraform apply
# ... when done demoing:
terraform destroy
```

## Running tests (what Jenkins runs)

```bash
pip install pytest
pytest tests/ -v
```

## Notes

- Database: controlled by `DATABASE_URL` (or `DB_HOST`/`DB_USER`/`DB_PASS`/`DB_NAME`)
  env vars. No env vars set -> falls back to local SQLite. This is what
  lets the exact same `app.py` run unmodified on your laptop, in Docker,
  and in Kubernetes.
- `/health` — used by Kubernetes liveness/readiness probes.
- `/metrics` — Prometheus scrape endpoint (Phase 8).
- Logs are written to stdout (for `docker logs`/`kubectl logs`) and to
  `logs/app.log` (for the ELK demo in Phase 9).

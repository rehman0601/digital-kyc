# HashiCorp Vault Server Configuration
# Runs Vault with local storage and exposes API endpoints for secret retrieval

# Enable the web-based management UI
ui = true

# Storage backend (file storage for simple, self-hosted deployment)
storage "file" {
  path = "/vault/data"
}

# TCP network listener
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = "true"  # Set to "false" and provide certs in production
}

# Disable cluster synchronization (only needed for HA clusters)
disable_mlock = true

# API Address used by redirect endpoints
api_addr = "http://127.0.0.1:8200"

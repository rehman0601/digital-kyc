# Variables for the Digital KYC AWS EKS & RDS Terraform configuration.

variable "aws_region" {
  description = "AWS region to deploy resources into"
  type        = string
  default     = "ap-south-1" # Mumbai - closest region for India
}

variable "eks_cluster_name" {
  description = "Name of the AWS EKS Cluster"
  type        = string
  default     = "kyc-verification-eks"
}

variable "s3_bucket_name" {
  description = "Globally unique S3 bucket name for storing KYC documents"
  type        = string
  default     = "digital-kyc-docs-storage-2026"
}

variable "db_name" {
  description = "The name of the RDS MySQL database"
  type        = string
  default     = "kyc_db"
}

variable "db_username" {
  description = "Admin username for the RDS MySQL database"
  type        = string
  default     = "kyc_user"
}

variable "db_password" {
  description = "Admin password for the RDS MySQL database"
  type        = string
  default     = "kyc_db_pass_2026"
  sensitive   = true
}

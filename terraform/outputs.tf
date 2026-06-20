# Terraform Outputs for EKS cluster and RDS MySQL setup

output "eks_cluster_name" {
  description = "The name of the AWS EKS Cluster"
  value       = aws_eks_cluster.kyc_eks.name
}

output "eks_cluster_endpoint" {
  description = "The endpoint URL for the AWS EKS Cluster API server"
  value       = aws_eks_cluster.kyc_eks.endpoint
}

output "rds_endpoint" {
  description = "The database connection endpoint for the RDS MySQL instance"
  value       = aws_db_instance.kyc_rds.endpoint
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket storing KYC documents"
  value       = aws_s3_bucket.kyc_documents.bucket
}

# Phase 6: Terraform - Infrastructure as Code for EKS and RDS
# Provisions AWS resources for a production-ready Digital KYC Platform:
# - VPC and networking (Internet Gateway, route tables, subnets across multiple AZs)
# - EKS Cluster and Worker Node group
# - RDS MySQL instance (managed DB layer)
# - S3 Bucket (secure, versioned, private storage for documents)
# - IAM Roles for EKS Cluster, Node Groups, and Rekognition access
# - CloudWatch Log Group for cluster logs

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ---------------------------------------------------------------------------
# Networking: VPC & Subnets
# ---------------------------------------------------------------------------
resource "aws_vpc" "kyc_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name    = "kyc-vpc"
    Project = "digital-kyc"
  }
}

resource "aws_internet_gateway" "kyc_igw" {
  vpc_id = aws_vpc.kyc_vpc.id

  tags = {
    Name    = "kyc-igw"
    Project = "digital-kyc"
  }
}

resource "aws_subnet" "kyc_subnet_a" {
  vpc_id            = aws_vpc.kyc_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name    = "kyc-subnet-a"
    Project = "digital-kyc"
  }
}

resource "aws_subnet" "kyc_subnet_b" {
  vpc_id            = aws_vpc.kyc_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"
  map_public_ip_on_launch = true

  tags = {
    Name    = "kyc-subnet-b"
    Project = "digital-kyc"
  }
}

resource "aws_route_table" "kyc_route_table" {
  vpc_id = aws_vpc.kyc_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.kyc_igw.id
  }

  tags = {
    Name    = "kyc-route-table"
    Project = "digital-kyc"
  }
}

resource "aws_route_table_association" "kyc_rta_a" {
  subnet_id      = aws_subnet.kyc_subnet_a.id
  route_table_id = aws_route_table.kyc_route_table.id
}

resource "aws_route_table_association" "kyc_rta_b" {
  subnet_id      = aws_subnet.kyc_subnet_b.id
  route_table_id = aws_route_table.kyc_route_table.id
}

# ---------------------------------------------------------------------------
# IAM Roles for EKS Cluster
# ---------------------------------------------------------------------------
resource "aws_iam_role" "eks_cluster_role" {
  name = "kyc-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster_role.name
}

# ---------------------------------------------------------------------------
# AWS EKS Cluster
# ---------------------------------------------------------------------------
resource "aws_eks_cluster" "kyc_eks" {
  name     = var.eks_cluster_name
  role_arn = aws_iam_role.eks_cluster_role.arn

  vpc_config {
    subnet_ids = [aws_subnet.kyc_subnet_a.id, aws_subnet.kyc_subnet_b.id]
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy
  ]
}

# ---------------------------------------------------------------------------
# IAM Roles for EKS Worker Nodes
# ---------------------------------------------------------------------------
resource "aws_iam_role" "eks_nodes_role" {
  name = "kyc-eks-nodes-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes_role.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodes_role.name
}

resource "aws_iam_role_policy_attachment" "eks_registry_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodes_role.name
}

# Custom IAM Policy to grant access to AWS Rekognition & Textract (OCR)
resource "aws_iam_policy" "eks_rekognition_policy" {
  name        = "kyc-eks-rekognition-policy"
  description = "Allows EKS worker nodes to use AWS Rekognition and Textract"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rekognition:DetectFaces",
          "rekognition:DetectText",
          "rekognition:CompareFaces",
          "textract:DetectDocumentText",
          "textract:AnalyzeDocument"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_nodes_rekognition" {
  policy_arn = aws_iam_policy.eks_rekognition_policy.arn
  role       = aws_iam_role.eks_nodes_role.name
}

# ---------------------------------------------------------------------------
# EKS Node Group (Worker Nodes)
# ---------------------------------------------------------------------------
resource "aws_eks_node_group" "kyc_nodes" {
  cluster_name    = aws_eks_cluster.kyc_eks.name
  node_group_name = "kyc-worker-nodes"
  node_role_arn   = aws_iam_role.eks_nodes_role.arn
  subnet_ids      = [aws_subnet.kyc_subnet_a.id, aws_subnet.kyc_subnet_b.id]

  scaling_config {
    desired_size = 2
    max_size     = 3
    min_size     = 1
  }

  instance_types = ["t3.medium"] # Standard production size for EKS worker nodes

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_registry_policy
  ]
}

# ---------------------------------------------------------------------------
# Database Layer: RDS MySQL
# ---------------------------------------------------------------------------
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "kyc-rds-subnet-group"
  subnet_ids = [aws_subnet.kyc_subnet_a.id, aws_subnet.kyc_subnet_b.id]

  tags = {
    Name    = "kyc-rds-subnet-group"
    Project = "digital-kyc"
  }
}

resource "aws_security_group" "rds_sg" {
  name        = "kyc-rds-sg"
  description = "Allow EKS nodes to communicate with RDS MySQL"
  vpc_id      = aws_vpc.kyc_vpc.id

  ingress {
    description = "MySQL access"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.kyc_vpc.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "kyc-rds-sg"
    Project = "digital-kyc"
  }
}

resource "aws_db_instance" "kyc_rds" {
  allocated_storage      = 20
  max_allocated_storage  = 100
  db_name                = var.db_name
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t3.micro"
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  skip_final_snapshot    = true

  tags = {
    Name    = "kyc-rds-instance"
    Project = "digital-kyc"
  }
}

# ---------------------------------------------------------------------------
# Cloud Storage: S3 Bucket (stores uploads securely)
# ---------------------------------------------------------------------------
resource "aws_s3_bucket" "kyc_documents" {
  bucket = var.s3_bucket_name

  tags = {
    Name    = "kyc-documents-storage"
    Project = "digital-kyc"
  }
}

resource "aws_s3_bucket_versioning" "kyc_documents_versioning" {
  bucket = aws_s3_bucket.kyc_documents.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "kyc_documents_block_public" {
  bucket                  = aws_s3_bucket.kyc_documents.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ---------------------------------------------------------------------------
# Observability: CloudWatch Logs
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "kyc_eks_logs" {
  name              = "/aws/eks/${var.eks_cluster_name}/cluster"
  retention_in_days = 7

  tags = {
    Name    = "kyc-eks-logs"
    Project = "digital-kyc"
  }
}

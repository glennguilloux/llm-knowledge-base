---
id: "devops-terraform-basics"
title: "Terraform Fundamentals: Resources, Modules, and State"
language: "yaml"
category: "devops"
subcategory: "infrastructure-as-code"
tags: ["terraform", "iac", "infrastructure", "hcl", "modules", "state", "cloud"]
version: "latest"
retrieval_hint: "Terraform resource variable output provider state module workspace infrastructure"
last_verified: "2026-05-24"
confidence: "high"
---

# Terraform Fundamentals: Resources, Modules, and State

## When to Use
- Provisioning cloud infrastructure (AWS, GCP, Azure) reproducibly
- Managing infrastructure as code across teams and environments
- Needing drift detection and plan-before-apply workflows
- Orchestrating multi-service deployments with dependency tracking

## Standard Pattern

```hcl
# --- variables.tf ---
variable "environment" {
  description = "Deployment environment"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

variable "instance_count" {
  description = "Number of EC2 instances"
  type        = number
  default     = 1
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}

# --- main.tf ---
terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "infra/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = merge(var.tags, {
      Environment = var.environment
      ManagedBy   = "terraform"
    })
  }
}

resource "aws_instance" "web" {
  count         = var.instance_count
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.public[count.index % length(aws_subnet.public)]

  tags = {
    Name = "web-${var.environment}-${count.index}"
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-*-amd64-server-*"]
  }
}

# --- outputs.tf ---
output "instance_ids" {
  description = "EC2 instance IDs"
  value       = aws_instance.web[*].id
}

output "public_ips" {
  description = "Public IP addresses"
  value       = aws_instance.web[*].public_ip
}
```

### Module Structure

```hcl
# --- modules/vpc/main.tf ---
variable "cidr_block" {
  type = string
}

variable "azs" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b"]
}

resource "aws_vpc" "this" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  tags = { Name = "vpc-${var.cidr_block}" }
}

resource "aws_subnet" "public" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.cidr_block, 8, count.index)
  availability_zone = var.azs[count.index]
  tags = { Name = "public-${var.azs[count.index]}" }
}

output "vpc_id" {
  value = aws_vpc.this.id
}

output "subnet_ids" {
  value = aws_subnet.public[*].id
}

# --- usage in root module ---
module "vpc" {
  source     = "./modules/vpc"
  cidr_block = "10.0.0.0/16"
  azs        = ["us-east-1a", "us-east-1b"]
}
```

## Common Mistakes

```hcl
# WRONG: Hardcoding credentials in provider block
provider "aws" {
  region     = "us-east-1"
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}

# CORRECT: Use environment variables or shared credentials file
provider "aws" {
  region = "us-east-1"
  # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY from env
  # Or use profile from ~/.aws/credentials
  profile = "production"
}
```

```hcl
# WRONG: Using count for complex resources that need stable identities
resource "aws_instance" "web" {
  count = 3
  # Deleting index 1 shifts all subsequent indices — causes unnecessary recreation
}

# CORRECT: Use for_each with a map for stable identity
resource "aws_instance" "web" {
  for_each = {
    web-a = { az = "us-east-1a", size = "t3.micro" }
    web-b = { az = "us-east-1b", size = "t3.micro" }
    web-c = { az = "us-east-1c", size = "t3.micro" }
  }
  ami               = data.aws_ami.ubuntu.id
  instance_type     = each.value.size
  availability_zone = each.value.az
  tags = { Name = each.key }
}
```

```hcl
# WRONG: Not locking state — concurrent applies cause corruption
terraform {
  backend "s3" {
    bucket = "my-state"
    key    = "terraform.tfstate"
    region = "us-east-1"
    # No locking configured!
  }
}

# CORRECT: Enable DynamoDB state locking
terraform {
  backend "s3" {
    bucket         = "my-state"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

## Gotchas
- `terraform plan` shows what will change — always review before `apply`; accidental `apply` in prod is unrecoverable without state backup
- `count` index shifting: removing index 1 from a 3-resource count forces recreation of indices 1 and 2 — use `for_each` for stable identities
- State files contain secrets (database passwords, API keys) — never commit to version control; use encrypted remote backends
- `terraform import` does NOT generate HCL — you must write matching config manually or use `terraform show` to reverse-engineer it
- Provider version pins (`~> 5.0`) prevent surprise upgrades but you must explicitly bump for new features; `>= 5.0` is dangerously loose
- `terraform destroy` targets can cascade — destroying a VPC destroys all subnets, instances, and security groups inside it
- Workspaces are NOT separate state files by default — they share the same backend config, just different state paths
- `depends_on` blocks prevent parallelism — use only when implicit dependencies fail; overuse slows applies dramatically

## Related
- devops/docker/dockerfile-patterns.md
- devops/kubernetes/basics.md

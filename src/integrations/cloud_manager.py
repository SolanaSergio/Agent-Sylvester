from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import json
import yaml
import logging
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

class CloudProvider(Enum):
    """Supported cloud providers"""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"

class ResourceType(Enum):
    """Types of cloud resources"""
    COMPUTE = "compute"  # EC2, GCE, Azure VM
    STORAGE = "storage"  # S3, GCS, Azure Blob
    DATABASE = "database"  # RDS, Cloud SQL, Azure SQL
    SERVERLESS = "serverless"  # Lambda, Cloud Functions, Azure Functions
    CONTAINER = "container"  # ECS/EKS, GKE, AKS
    CDN = "cdn"  # CloudFront, Cloud CDN, Azure CDN
    DNS = "dns"  # Route53, Cloud DNS, Azure DNS
    MONITORING = "monitoring"  # CloudWatch, Cloud Monitoring, Azure Monitor

@dataclass
class ResourceConfig:
    """Configuration for cloud resources"""
    type: ResourceType
    name: str
    provider: CloudProvider
    region: str
    specs: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)

@dataclass
class DeploymentConfig:
    """Configuration for cloud deployments"""
    name: str
    provider: CloudProvider
    region: str
    resources: List[ResourceConfig]
    environment: str = "development"
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)

class CloudManager:
    """Manages cloud service integrations, deployments, and resources"""
    
    def __init__(self, config_dir: Union[str, Path]):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Provider-specific configuration directories
        self.aws_config_dir = self.config_dir / "aws"
        self.gcp_config_dir = self.config_dir / "gcp"
        self.azure_config_dir = self.config_dir / "azure"
        
        for directory in [self.aws_config_dir, self.gcp_config_dir, self.azure_config_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Initialize templates
        self._init_templates()
        
        logging.info(f"Cloud Manager initialized with config dir: {config_dir}")
        
    def _init_templates(self):
        """Initialize cloud service templates"""
        templates = {
            'aws': {
                'cloudformation.yaml.jinja2': '''
AWSTemplateFormatVersion: '2010-09-09'
Description: {{deployment.name}} - {{deployment.environment}} environment

Resources:
  {% for resource in deployment.resources %}
  {{resource.name}}:
    Type: AWS::{{resource.type.value|title}}::Instance
    Properties:
      {% for key, value in resource.specs.items() %}
      {{key}}: {{value|tojson}}
      {% endfor %}
      Tags:
        {% for key, value in resource.tags.items() %}
        - Key: {{key}}
          Value: {{value}}
        {% endfor %}
  {% endfor %}

Outputs:
  {% for resource in deployment.resources %}
  {{resource.name}}Id:
    Description: ID of {{resource.name}}
    Value: !Ref {{resource.name}}
  {% endfor %}
''',
                'terraform.tf.jinja2': '''
provider "aws" {
  region = "{{deployment.region}}"
}

{% for resource in deployment.resources %}
resource "aws_{{resource.type.value}}_instance" "{{resource.name}}" {
  {% for key, value in resource.specs.items() %}
  {{key}} = {{value|tojson}}
  {% endfor %}
  
  tags = {
    {% for key, value in resource.tags.items() %}
    {{key}} = "{{value}}"
    {% endfor %}
  }
}
{% endfor %}

output "resource_ids" {
  value = {
    {% for resource in deployment.resources %}
    {{resource.name}} = aws_{{resource.type.value}}_instance.{{resource.name}}.id
    {% endfor %}
  }
}
'''
            },
            'gcp': {
                'deployment-manager.yaml.jinja2': '''
resources:
{% for resource in deployment.resources %}
- name: {{resource.name}}
  type: {{resource.type.value}}.googleapis.com/projects/{{project_id}}/{{resource.type.value}}s
  properties:
    {% for key, value in resource.specs.items() %}
    {{key}}: {{value|tojson}}
    {% endfor %}
    labels:
      {% for key, value in resource.tags.items() %}
      {{key}}: {{value}}
      {% endfor %}
{% endfor %}
''',
                'terraform.tf.jinja2': '''
provider "google" {
  project = "{{project_id}}"
  region  = "{{deployment.region}}"
}

{% for resource in deployment.resources %}
resource "google_{{resource.type.value}}" "{{resource.name}}" {
  name = "{{resource.name}}"
  
  {% for key, value in resource.specs.items() %}
  {{key}} = {{value|tojson}}
  {% endfor %}
  
  labels = {
    {% for key, value in resource.tags.items() %}
    {{key}} = "{{value}}"
    {% endfor %}
  }
}
{% endfor %}

output "resource_ids" {
  value = {
    {% for resource in deployment.resources %}
    {{resource.name}} = google_{{resource.type.value}}.{{resource.name}}.id
    {% endfor %}
  }
}
'''
            },
            'azure': {
                'arm-template.json.jinja2': '''
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {},
  "resources": [
    {% for resource in deployment.resources %}
    {
      "name": "{{resource.name}}",
      "type": "Microsoft.{{resource.type.value|title}}/{{resource.type.value}}s",
      "apiVersion": "2021-04-01",
      "location": "{{deployment.region}}",
      "properties": {{resource.specs|tojson}},
      "tags": {{resource.tags|tojson}}
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  ],
  "outputs": {
    {% for resource in deployment.resources %}
    "{{resource.name}}Id": {
      "type": "string",
      "value": "[resourceId('Microsoft.{{resource.type.value|title}}/{{resource.type.value}}s', '{{resource.name}}')]"
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  }
}
''',
                'terraform.tf.jinja2': '''
provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "main" {
  name     = "{{deployment.name}}"
  location = "{{deployment.region}}"
}

{% for resource in deployment.resources %}
resource "azurerm_{{resource.type.value}}" "{{resource.name}}" {
  name                = "{{resource.name}}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  
  {% for key, value in resource.specs.items() %}
  {{key}} = {{value|tojson}}
  {% endfor %}
  
  tags = {
    {% for key, value in resource.tags.items() %}
    {{key}} = "{{value}}"
    {% endfor %}
  }
}
{% endfor %}

output "resource_ids" {
  value = {
    {% for resource in deployment.resources %}
    {{resource.name}} = azurerm_{{resource.type.value}}.{{resource.name}}.id
    {% endfor %}
  }
}
'''
            }
        }
        
        for provider, provider_templates in templates.items():
            provider_dir = self.config_dir / provider / "templates"
            provider_dir.mkdir(parents=True, exist_ok=True)
            
            for name, content in provider_templates.items():
                template_file = provider_dir / name
                if not template_file.exists():
                    template_file.write_text(content)
                    
    async def create_deployment(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Create a new cloud deployment"""
        try:
            if config.provider == CloudProvider.AWS:
                return await self._create_aws_deployment(config)
            elif config.provider == CloudProvider.GCP:
                return await self._create_gcp_deployment(config)
            elif config.provider == CloudProvider.AZURE:
                return await self._create_azure_deployment(config)
            else:
                raise ValueError(f"Unsupported cloud provider: {config.provider}")
                
        except Exception as e:
            logging.error(f"Error creating deployment: {str(e)}")
            raise
            
    async def _create_aws_deployment(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Create AWS deployment using CloudFormation"""
        try:
            # Generate CloudFormation template
            template_file = self.aws_config_dir / f"{config.name}_cloudformation.yaml"
            terraform_file = self.aws_config_dir / f"{config.name}_terraform.tf"
            
            # Generate CloudFormation template
            cf_template = {
                "AWSTemplateFormatVersion": "2010-09-09",
                "Description": f"CloudFormation template for {config.name}",
                "Parameters": {},
                "Resources": {},
                "Outputs": {}
            }
            
            # Process each resource
            for resource in config.resources:
                resource_name = resource.name.replace("-", "").replace("_", "")
                
                if resource.type == ResourceType.COMPUTE:
                    # Add EC2 instance
                    cf_template["Resources"][f"{resource_name}Instance"] = {
                        "Type": "AWS::EC2::Instance",
                        "Properties": {
                            "InstanceType": resource.specs.get("instance_type", "t2.micro"),
                            "ImageId": resource.specs.get("ami_id", "ami-0c55b159cbfafe1f0"),
                            "Tags": [{"Key": k, "Value": v} for k, v in resource.tags.items()]
                        }
                    }
                    
                elif resource.type == ResourceType.STORAGE:
                    # Add S3 bucket
                    cf_template["Resources"][f"{resource_name}Bucket"] = {
                        "Type": "AWS::S3::Bucket",
                        "Properties": {
                            "BucketName": resource.name.lower(),
                            "Tags": [{"Key": k, "Value": v} for k, v in resource.tags.items()]
                        }
                    }
                    
                elif resource.type == ResourceType.DATABASE:
                    # Add RDS instance
                    cf_template["Resources"][f"{resource_name}DB"] = {
                        "Type": "AWS::RDS::DBInstance",
                        "Properties": {
                            "Engine": resource.specs.get("engine", "mysql"),
                            "DBInstanceClass": resource.specs.get("instance_class", "db.t2.micro"),
                            "AllocatedStorage": resource.specs.get("storage", 20),
                            "Tags": [{"Key": k, "Value": v} for k, v in resource.tags.items()]
                        }
                    }
                    
                elif resource.type == ResourceType.SERVERLESS:
                    # Add Lambda function
                    cf_template["Resources"][f"{resource_name}Function"] = {
                        "Type": "AWS::Lambda::Function",
                        "Properties": {
                            "Handler": resource.specs.get("handler", "index.handler"),
                            "Role": resource.specs.get("role", ""),
                            "Code": {
                                "S3Bucket": resource.specs.get("code_bucket", ""),
                                "S3Key": resource.specs.get("code_key", "")
                            },
                            "Runtime": resource.specs.get("runtime", "nodejs14.x"),
                            "Tags": [{"Key": k, "Value": v} for k, v in resource.tags.items()]
                        }
                    }
            
            # Write template to file
            template_file.write_text(yaml.dump(cf_template))
            
            # Would use boto3 to create/update stack here
            # For now, return deployment details
            return {
                "deployment_id": f"aws-{config.name}-{config.version}",
                "provider": config.provider.value,
                "status": "pending",
                "resources": [r.name for r in config.resources],
                "template_file": str(template_file)
            }
            
        except Exception as e:
            logging.error(f"Error creating AWS deployment: {str(e)}")
            raise
            
    async def _create_gcp_deployment(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Create GCP deployment using Deployment Manager"""
        try:
            # Generate Deployment Manager template
            template_file = self.gcp_config_dir / f"{config.name}_deployment.yaml"
            terraform_file = self.gcp_config_dir / f"{config.name}_terraform.tf"
            
            # Generate Deployment Manager template
            dm_template = {
                "imports": [],
                "resources": []
            }
            
            # Process each resource
            for resource in config.resources:
                if resource.type == ResourceType.COMPUTE:
                    # Add Compute Engine instance
                    instance = {
                        "name": resource.name,
                        "type": "compute.v1.instance",
                        "properties": {
                            "zone": f"{config.region}-a",
                            "machineType": f"zones/{config.region}-a/machineTypes/{resource.specs.get('machine_type', 'n1-standard-1')}",
                            "disks": [{
                                "boot": True,
                                "autoDelete": True,
                                "initializeParams": {
                                    "sourceImage": resource.specs.get("image", "projects/debian-cloud/global/images/debian-10")
                                }
                            }],
                            "networkInterfaces": [{
                                "network": "global/networks/default",
                                "accessConfigs": [{"name": "External NAT", "type": "ONE_TO_ONE_NAT"}]
                            }],
                            "labels": resource.tags
                        }
                    }
                    dm_template["resources"].append(instance)
                    
                elif resource.type == ResourceType.STORAGE:
                    # Add Cloud Storage bucket
                    bucket = {
                        "name": resource.name.lower(),
                        "type": "storage.v1.bucket",
                        "properties": {
                            "location": config.region,
                            "storageClass": resource.specs.get("storage_class", "STANDARD"),
                            "labels": resource.tags
                        }
                    }
                    dm_template["resources"].append(bucket)
                    
                elif resource.type == ResourceType.DATABASE:
                    # Add Cloud SQL instance
                    database = {
                        "name": resource.name,
                        "type": "sqladmin.v1beta4.instance",
                        "properties": {
                            "region": config.region,
                            "databaseVersion": resource.specs.get("version", "MYSQL_5_7"),
                            "settings": {
                                "tier": resource.specs.get("tier", "db-f1-micro"),
                                "dataDiskSizeGb": resource.specs.get("storage", "10"),
                                "userLabels": resource.tags
                            }
                        }
                    }
                    dm_template["resources"].append(database)
                    
                elif resource.type == ResourceType.SERVERLESS:
                    # Add Cloud Function
                    function = {
                        "name": resource.name,
                        "type": "cloudfunctions.v1.function",
                        "properties": {
                            "location": config.region,
                            "runtime": resource.specs.get("runtime", "nodejs14"),
                            "entryPoint": resource.specs.get("entry_point", "main"),
                            "sourceArchiveUrl": resource.specs.get("source_archive_url", ""),
                            "labels": resource.tags
                        }
                    }
                    dm_template["resources"].append(function)
            
            # Write template to file
            template_file.write_text(yaml.dump(dm_template))
            
            # Would use google-cloud-deploy to create deployment here
            # For now, return deployment details
            return {
                "deployment_id": f"gcp-{config.name}-{config.version}",
                "provider": config.provider.value,
                "status": "pending",
                "resources": [r.name for r in config.resources],
                "template_file": str(template_file)
            }
            
        except Exception as e:
            logging.error(f"Error creating GCP deployment: {str(e)}")
            raise
            
    async def _create_azure_deployment(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Create Azure deployment using ARM templates"""
        try:
            # Generate ARM template
            template_file = self.azure_config_dir / f"{config.name}_arm.json"
            terraform_file = self.azure_config_dir / f"{config.name}_terraform.tf"
            
            # Generate ARM template
            arm_template = {
                "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
                "contentVersion": "1.0.0.0",
                "parameters": {},
                "variables": {},
                "resources": []
            }
            
            # Process each resource
            for resource in config.resources:
                if resource.type == ResourceType.COMPUTE:
                    # Add Virtual Machine
                    vm = {
                        "type": "Microsoft.Compute/virtualMachines",
                        "apiVersion": "2021-03-01",
                        "name": resource.name,
                        "location": config.region,
                        "properties": {
                            "hardwareProfile": {
                                "vmSize": resource.specs.get("vm_size", "Standard_DS1_v2")
                            },
                            "osProfile": {
                                "computerName": resource.name,
                                "adminUsername": resource.specs.get("admin_username", "azureuser"),
                                "adminPassword": resource.specs.get("admin_password", "")
                            },
                            "storageProfile": {
                                "imageReference": {
                                    "publisher": "Canonical",
                                    "offer": "UbuntuServer",
                                    "sku": "18.04-LTS",
                                    "version": "latest"
                                }
                            },
                            "networkProfile": {
                                "networkInterfaces": [{
                                    "id": f"[resourceId('Microsoft.Network/networkInterfaces', '{resource.name}-nic')]"
                                }]
                            }
                        },
                        "tags": resource.tags
                    }
                    arm_template["resources"].append(vm)
                    
                elif resource.type == ResourceType.STORAGE:
                    # Add Storage Account
                    storage = {
                        "type": "Microsoft.Storage/storageAccounts",
                        "apiVersion": "2021-04-01",
                        "name": resource.name.lower().replace("-", ""),
                        "location": config.region,
                        "sku": {
                            "name": resource.specs.get("sku", "Standard_LRS")
                        },
                        "kind": "StorageV2",
                        "properties": {},
                        "tags": resource.tags
                    }
                    arm_template["resources"].append(storage)
                    
                elif resource.type == ResourceType.DATABASE:
                    # Add Azure SQL Database
                    database = {
                        "type": "Microsoft.Sql/servers/databases",
                        "apiVersion": "2021-02-01-preview",
                        "name": f"{resource.name}-server/{resource.name}-db",
                        "location": config.region,
                        "sku": {
                            "name": resource.specs.get("sku", "Basic"),
                            "tier": resource.specs.get("tier", "Basic")
                        },
                        "properties": {
                            "collation": resource.specs.get("collation", "SQL_Latin1_General_CP1_CI_AS"),
                            "maxSizeBytes": resource.specs.get("max_size_bytes", 1073741824)
                        },
                        "tags": resource.tags
                    }
                    arm_template["resources"].append(database)
                    
                elif resource.type == ResourceType.SERVERLESS:
                    # Add Function App
                    function = {
                        "type": "Microsoft.Web/sites",
                        "apiVersion": "2021-02-01",
                        "name": resource.name,
                        "location": config.region,
                        "kind": "functionapp",
                        "properties": {
                            "siteConfig": {
                                "appSettings": [
                                    {"name": "FUNCTIONS_WORKER_RUNTIME", "value": resource.specs.get("runtime", "node")},
                                    {"name": "WEBSITE_NODE_DEFAULT_VERSION", "value": "~14"}
                                ]
                            }
                        },
                        "tags": resource.tags
                    }
                    arm_template["resources"].append(function)
            
            # Write template to file
            template_file.write_text(json.dumps(arm_template, indent=2))
            
            # Would use azure-mgmt-resource to create deployment here
            # For now, return deployment details
            return {
                "deployment_id": f"azure-{config.name}-{config.version}",
                "provider": config.provider.value,
                "status": "pending",
                "resources": [r.name for r in config.resources],
                "template_file": str(template_file)
            }
            
        except Exception as e:
            logging.error(f"Error creating Azure deployment: {str(e)}")
            raise
            
    async def monitor_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """Monitor deployment status and resources"""
        try:
            # Parse deployment ID to get provider and name
            provider, name, version = deployment_id.split("-")
            provider = CloudProvider(provider.lower())
            
            status = {
                "deployment_id": deployment_id,
                "status": "unknown",
                "resources": [],
                "last_updated": datetime.now().isoformat()
            }
            
            if provider == CloudProvider.AWS:
                # Check CloudFormation stack status
                stack_name = f"{name}-{version}"
                status["status"] = "running"  # Would use boto3 to get real status
                
            elif provider == CloudProvider.GCP:
                # Check Deployment Manager status
                deployment_name = f"{name}-{version}"
                status["status"] = "running"  # Would use google-cloud-deploy to get real status
                
            elif provider == CloudProvider.AZURE:
                # Check ARM deployment status
                resource_group = f"{name}-{version}"
                status["status"] = "running"  # Would use azure-mgmt-resource to get real status
            
            return status
            
        except Exception as e:
            logging.error(f"Error monitoring deployment {deployment_id}: {str(e)}")
            raise

    async def update_deployment(self, deployment_id: str, config: DeploymentConfig) -> Dict[str, Any]:
        """Update an existing deployment"""
        try:
            # Validate deployment exists
            current_status = await self.monitor_deployment(deployment_id)
            if current_status["status"] == "unknown":
                raise ValueError(f"Deployment {deployment_id} not found")
                
            # Create new deployment with updated config
            if config.provider == CloudProvider.AWS:
                return await self._create_aws_deployment(config)
            elif config.provider == CloudProvider.GCP:
                return await self._create_gcp_deployment(config)
            elif config.provider == CloudProvider.AZURE:
                return await self._create_azure_deployment(config)
                
            raise ValueError(f"Unsupported cloud provider: {config.provider}")
            
        except Exception as e:
            logging.error(f"Error updating deployment {deployment_id}: {str(e)}")
            raise

    async def delete_deployment(self, deployment_id: str) -> bool:
        """Delete a deployment and its resources"""
        try:
            # Parse deployment ID
            provider, name, version = deployment_id.split("-")
            provider = CloudProvider(provider.lower())
            
            if provider == CloudProvider.AWS:
                # Delete CloudFormation stack
                stack_name = f"{name}-{version}"
                # Would use boto3 to delete stack
                return True
                
            elif provider == CloudProvider.GCP:
                # Delete Deployment Manager deployment
                deployment_name = f"{name}-{version}"
                # Would use google-cloud-deploy to delete deployment
                return True
                
            elif provider == CloudProvider.AZURE:
                # Delete ARM deployment
                resource_group = f"{name}-{version}"
                # Would use azure-mgmt-resource to delete deployment
                return True
                
            raise ValueError(f"Unsupported cloud provider: {provider}")
            
        except Exception as e:
            logging.error(f"Error deleting deployment {deployment_id}: {str(e)}")
            raise

    async def get_resource_metrics(self, resource_id: str) -> Dict[str, Any]:
        """Get monitoring metrics for a resource"""
        try:
            # Parse resource ID to get provider and type
            provider, resource_type, name = resource_id.split(":")
            provider = CloudProvider(provider.lower())
            resource_type = ResourceType(resource_type.lower())
            
            metrics = {
                "resource_id": resource_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": {}
            }
            
            if provider == CloudProvider.AWS:
                # Get CloudWatch metrics
                if resource_type == ResourceType.COMPUTE:
                    metrics["metrics"] = {
                        "cpu_utilization": 0.0,
                        "memory_utilization": 0.0,
                        "network_in": 0.0,
                        "network_out": 0.0
                    }
                elif resource_type == ResourceType.DATABASE:
                    metrics["metrics"] = {
                        "connections": 0,
                        "cpu_utilization": 0.0,
                        "free_storage": 0.0
                    }
                # Add more resource type metrics as needed
                
            elif provider == CloudProvider.GCP:
                # Get Cloud Monitoring metrics
                if resource_type == ResourceType.COMPUTE:
                    metrics["metrics"] = {
                        "cpu_utilization": 0.0,
                        "memory_utilization": 0.0,
                        "network_throughput": 0.0
                    }
                # Add more resource type metrics as needed
                
            elif provider == CloudProvider.AZURE:
                # Get Azure Monitor metrics
                if resource_type == ResourceType.COMPUTE:
                    metrics["metrics"] = {
                        "percentage_cpu": 0.0,
                        "memory_usage": 0.0,
                        "network_in_total": 0.0,
                        "network_out_total": 0.0
                    }
                # Add more resource type metrics as needed
            
            return metrics
            
        except Exception as e:
            logging.error(f"Error getting metrics for resource {resource_id}: {str(e)}")
            raise 
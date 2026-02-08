#!/usr/bin/env python3
"""
Script to create AgentCore Runtime endpoints.
Usage: python create_endpoint.py --agent-runtime-id <id> --name <name> --version <version>
"""

import boto3
import argparse
import sys

def create_endpoint(agent_runtime_id, name, version=None, description=None, tags=None, region='eu-central-1'):
    """Create a new AgentCore Runtime endpoint."""
    
    client = boto3.client('bedrock-agentcore-control', region_name=region)
    
    try:
        print(f"Creating endpoint '{name}'...")
        
        request_params = {
            'agentRuntimeId': agent_runtime_id,
            'name': name
        }
        
        if version:
            request_params['agentRuntimeVersion'] = str(version)
            print(f"  Target Version: {version}")
        else:
            print(f"  Target Version: Latest")
        
        if description:
            request_params['description'] = description
            
        if tags:
            request_params['tags'] = tags
        
        response = client.create_agent_runtime_endpoint(**request_params)
        
        print(f"\n✓ Endpoint created successfully!")
        print(f"  Endpoint Name: {response['endpointName']}")
        print(f"  Status: {response['status']}")
        print(f"  Target Version: {response.get('targetVersion', 'Latest')}")
        print(f"  Endpoint ARN: {response['agentRuntimeEndpointArn']}")
        print(f"  Created At: {response['createdAt']}")
        
        return response
        
    except client.exceptions.ConflictException:
        print(f"✗ Error: Endpoint '{name}' already exists")
        sys.exit(1)
    except client.exceptions.ResourceNotFoundException:
        print(f"✗ Error: Agent runtime not found")
        sys.exit(1)
    except client.exceptions.ValidationException as e:
        print(f"✗ Validation Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

def delete_endpoint(agent_runtime_id, endpoint_name, region='eu-central-1'):
    """Delete an AgentCore Runtime endpoint."""
    
    client = boto3.client('bedrock-agentcore-control', region_name=region)
    
    try:
        print(f"Deleting endpoint '{endpoint_name}'...")
        
        response = client.delete_agent_runtime_endpoint(
            agentRuntimeId=agent_runtime_id,
            endpointName=endpoint_name
        )
        
        print(f"✓ Endpoint deletion initiated")
        print(f"  Status: {response.get('status', 'DELETING')}")
        
        return response
        
    except client.exceptions.ResourceNotFoundException:
        print(f"✗ Error: Endpoint not found")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

def get_endpoint(agent_runtime_id, endpoint_name, region='eu-central-1'):
    """Get details of a specific endpoint."""
    
    client = boto3.client('bedrock-agentcore-control', region_name=region)
    
    try:
        response = client.get_agent_runtime_endpoint(
            agentRuntimeId=agent_runtime_id,
            endpointName=endpoint_name
        )
        
        print(f"\nEndpoint Details:")
        print("-" * 80)
        print(f"  Name: {response['name']}")
        print(f"  Status: {response['status']}")
        print(f"  Live Version: {response.get('liveVersion', 'N/A')}")
        print(f"  Target Version: {response.get('targetVersion', 'N/A')}")
        print(f"  Description: {response.get('description', 'N/A')}")
        print(f"  Created At: {response['createdAt']}")
        print(f"  Last Updated: {response['lastUpdatedAt']}")
        print(f"  Endpoint ARN: {response['agentRuntimeEndpointArn']}")
        print("-" * 80)
        
        return response
        
    except client.exceptions.ResourceNotFoundException:
        print(f"✗ Error: Endpoint not found")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

def list_endpoints(agent_runtime_id, region='eu-central-1'):
    """List all endpoints for an agent runtime."""
    
    client = boto3.client('bedrock-agentcore-control', region_name=region)
    
    try:
        response = client.list_agent_runtime_endpoints(
            agentRuntimeId=agent_runtime_id
        )
        
        endpoints = response.get('agentRuntimeEndpoints', [])
        
        if not endpoints:
            print(f"\nNo endpoints found for {agent_runtime_id}")
            return
        
        print(f"\nEndpoints for {agent_runtime_id}:")
        print("=" * 80)
        
        for endpoint in endpoints:
            print(f"  Name: {endpoint['name']}")
            print(f"  Status: {endpoint['status']}")
            print(f"  Live Version: {endpoint.get('liveVersion', 'N/A')}")
            print(f"  Target Version: {endpoint.get('targetVersion', 'N/A')}")
            if endpoint.get('description'):
                print(f"  Description: {endpoint['description']}")
            print("-" * 80)
            
    except Exception as e:
        print(f"✗ Error listing endpoints: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Create and manage AgentCore Runtime endpoints',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new endpoint pointing to version 3
  python create_endpoint.py --agent-runtime-id testAgent-71evTo5Zf8 --name staging --version 3
  
  # Create endpoint with description
  python create_endpoint.py --agent-runtime-id testAgent-71evTo5Zf8 --name dev --version 2 --description "Development endpoint"
  
  # Create endpoint pointing to latest version
  python create_endpoint.py --agent-runtime-id testAgent-71evTo5Zf8 --name latest
  
  # List all endpoints
  python create_endpoint.py --agent-runtime-id testAgent-71evTo5Zf8 --list
  
  # Get specific endpoint details
  python create_endpoint.py --agent-runtime-id testAgent-71evTo5Zf8 --get dev
  
  # Delete an endpoint
  python create_endpoint.py --agent-runtime-id testAgent-71evTo5Zf8 --delete staging
        """
    )
    
    parser.add_argument('--agent-runtime-id', required=True, help='Agent Runtime ID (e.g., testAgent-71evTo5Zf8)')
    parser.add_argument('--name', help='Endpoint name (e.g., dev, staging, prod)')
    parser.add_argument('--version', help='Version number to point to (e.g., 3). Omit for latest version')
    parser.add_argument('--description', help='Description of the endpoint')
    parser.add_argument('--region', default='eu-central-1', help='AWS region (default: eu-central-1)')
    parser.add_argument('--list', action='store_true', help='List all endpoints')
    parser.add_argument('--get', metavar='ENDPOINT_NAME', help='Get details of a specific endpoint')
    parser.add_argument('--delete', metavar='ENDPOINT_NAME', help='Delete a specific endpoint')
    parser.add_argument('--tag', action='append', metavar='KEY=VALUE', help='Add tags (can be used multiple times)')
    
    args = parser.parse_args()
    
    if args.list:
        list_endpoints(args.agent_runtime_id, args.region)
    elif args.get:
        get_endpoint(args.agent_runtime_id, args.get, args.region)
    elif args.delete:
        delete_endpoint(args.agent_runtime_id, args.delete, args.region)
    elif args.name:
        tags = None
        if args.tag:
            tags = {}
            for tag in args.tag:
                if '=' not in tag:
                    print(f"Error: Invalid tag format '{tag}'. Use KEY=VALUE")
                    sys.exit(1)
                key, value = tag.split('=', 1)
                tags[key] = value
        
        create_endpoint(
            args.agent_runtime_id,
            args.name,
            args.version,
            args.description,
            tags,
            args.region
        )
    else:
        print("Error: Specify --name to create, --list to list, --get to view, or --delete to remove an endpoint")
        parser.print_help()
        sys.exit(1)

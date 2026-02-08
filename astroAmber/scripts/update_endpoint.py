#!/usr/bin/env python3
"""
Script to update AgentCore Runtime endpoint to a specific version.
Usage: python update_endpoint.py --agent-runtime-id <id> --endpoint-name <name> --version <version>
"""

import boto3
import argparse
import sys

def update_endpoint(agent_runtime_id, endpoint_name, version, region='eu-central-1'):
    """Update an AgentCore Runtime endpoint to point to a specific version."""
    
    client = boto3.client('bedrock-agentcore-control', region_name=region)
    
    try:
        print(f"Updating endpoint '{endpoint_name}' to version {version}...")
        
        response = client.update_agent_runtime_endpoint(
            agentRuntimeId=agent_runtime_id,
            endpointName=endpoint_name,
            agentRuntimeVersion=str(version)
        )
        
        print(f"\n✓ Endpoint update initiated successfully!")
        print(f"  Status: {response['status']}")
        print(f"  Live Version: {response.get('liveVersion', 'N/A')}")
        print(f"  Target Version: {response.get('targetVersion', 'N/A')}")
        print(f"  Last Updated: {response['lastUpdatedAt']}")
        
        return response
        
    except client.exceptions.ResourceNotFoundException:
        print(f"✗ Error: Agent runtime or endpoint not found")
        sys.exit(1)
    except client.exceptions.ValidationException as e:
        print(f"✗ Validation Error: {e}")
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
        
        print(f"\nEndpoints for {agent_runtime_id}:")
        print("-" * 80)
        
        for endpoint in response.get('agentRuntimeEndpoints', []):
            print(f"  Name: {endpoint['name']}")
            print(f"  Status: {endpoint['status']}")
            print(f"  Live Version: {endpoint.get('liveVersion', 'N/A')}")
            print(f"  Target Version: {endpoint.get('targetVersion', 'N/A')}")
            print("-" * 80)
            
    except Exception as e:
        print(f"✗ Error listing endpoints: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update AgentCore Runtime endpoint version')
    parser.add_argument('--agent-runtime-id', required=True, help='Agent Runtime ID (e.g., testAgent-71evTo5Zf8)')
    parser.add_argument('--endpoint-name', help='Endpoint name (e.g., dev, DEFAULT)')
    parser.add_argument('--version', help='Version number to deploy (e.g., 4)')
    parser.add_argument('--region', default='eu-central-1', help='AWS region (default: eu-central-1)')
    parser.add_argument('--list', action='store_true', help='List all endpoints')
    
    args = parser.parse_args()
    
    if args.list:
        list_endpoints(args.agent_runtime_id, args.region)
    elif args.endpoint_name and args.version:
        update_endpoint(args.agent_runtime_id, args.endpoint_name, args.version, args.region)
    else:
        print("Error: Either use --list or provide both --endpoint-name and --version")
        parser.print_help()
        sys.exit(1)

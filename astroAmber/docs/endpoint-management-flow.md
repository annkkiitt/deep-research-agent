# Complete Flow: Dev and Prod Endpoint Management

This guide provides a comprehensive workflow for managing multiple endpoints (dev, prod) in AWS Bedrock AgentCore, enabling safe deployment practices with proper testing and rollback capabilities.

## Overview

AgentCore uses **versioned deployments** with **endpoints** that can point to specific versions:
- **DEFAULT endpoint**: Automatically points to the latest deployed version
- **Custom endpoints** (dev, prod): Manually controlled to point to specific versions
- **Immutable versions**: Each deployment creates a new version that cannot be changed

## Prerequisites

- AgentCore CLI installed and configured
- Python scripts for endpoint management:
  - `scripts/create_endpoint.py`
  - `scripts/update_endpoint.py`
- AWS credentials configured
- Agent runtime ID from your `.bedrock_agentcore.yaml`

## Initial Setup (One-Time)

### Step 1: Configure and Deploy Your Agent

```bash
# Configure your agent
agentcore configure --entrypoint src/main.py --name astroAmber

# First deployment (creates version 1)
agentcore deploy --agent astroAmber
```

### Step 2: Create Dev Endpoint

```bash
# Create dev endpoint pointing to version 1
python scripts/create_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --name dev \
  --version 1 \
  --description "Development environment for testing new features"
```

### Step 3: Create Prod Endpoint

```bash
# Create prod endpoint pointing to version 1
python scripts/create_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --name prod \
  --version 1 \
  --description "Production environment - stable version"
```

### Step 4: Verify Endpoints

```bash
# List all endpoints
python scripts/create_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --list
```

**Expected Result:**
- **DEFAULT** → version 1 (auto-managed)
- **dev** → version 1
- **prod** → version 1

---

## Regular Development Workflow

### Scenario: Deploy New Feature to Dev First

#### Step 1: Make Code Changes

```bash
# Edit your code in src/main.py
# Test locally if needed (optional)
agentcore deploy --local
```

#### Step 2: Deploy to AWS (Creates New Version)

```bash
# Deploy creates version 2
agentcore deploy --agent astroAmber

# DEFAULT endpoint automatically updates to version 2
```

#### Step 3: Update Dev Endpoint to New Version

```bash
# Point dev to version 2 for testing
python scripts/update_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --endpoint-name dev \
  --version 2
```

#### Step 4: Test on Dev Endpoint

```bash
# Test your changes on dev
agentcore invoke '{"prompt": "test new feature"}' --agent astroAmber

# Note: This invokes DEFAULT (version 2)
# To invoke dev specifically, you need to use the endpoint ARN or session routing
```

#### Step 5: Verify Endpoint Status

```bash
# Check all endpoints
python scripts/create_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --list
```

**Current State:**
- **DEFAULT** → version 2
- **dev** → version 2 (testing)
- **prod** → version 1 (stable)

#### Step 6: Promote to Production

```bash
# After testing on dev, promote to prod
python scripts/update_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --endpoint-name prod \
  --version 2
```

**Final State:**
- **DEFAULT** → version 2
- **dev** → version 2
- **prod** → version 2

---

## Rollback Scenario

### If Version 2 Has Issues:

```bash
# Rollback dev to version 1
python scripts/update_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --endpoint-name dev \
  --version 1

# Keep prod on version 1 (no action needed)
```

### Emergency Prod Rollback:

```bash
# Rollback prod to previous stable version
python scripts/update_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --endpoint-name prod \
  --version 1
```

---

## Advanced Workflow: Canary Deployment

### Step 1: Deploy New Version

```bash
agentcore deploy --agent astroAmber  # Creates version 3
```

### Step 2: Test on Dev

```bash
python scripts/update_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --endpoint-name dev \
  --version 3
```

### Step 3: Create Canary Endpoint

```bash
# Create canary endpoint for limited prod testing
python scripts/create_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --name canary \
  --version 3 \
  --description "Canary deployment for gradual rollout"
```

### Step 4: Monitor Canary

```bash
# Monitor canary performance
# If successful, promote to prod
python scripts/update_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --endpoint-name prod \
  --version 3

# Delete canary endpoint
python scripts/create_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --delete canary
```

---

## Quick Reference Commands

### Check Current State
```bash
python scripts/create_endpoint.py --agent-runtime-id testAgent-71evTo5Zf8 --list
```

### Get Specific Endpoint Details
```bash
python scripts/create_endpoint.py --agent-runtime-id testAgent-71evTo5Zf8 --get prod
```

### Deploy New Version
```bash
agentcore deploy --agent astroAmber
```

### Update Dev
```bash
python scripts/update_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --endpoint-name dev \
  --version <VERSION>
```

### Update Prod
```bash
python scripts/update_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --endpoint-name prod \
  --version <VERSION>
```

### Create New Endpoint
```bash
python scripts/create_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --name <ENDPOINT_NAME> \
  --version <VERSION> \
  --description "<DESCRIPTION>"
```

### Delete Endpoint
```bash
python scripts/create_endpoint.py \
  --agent-runtime-id testAgent-71evTo5Zf8 \
  --delete <ENDPOINT_NAME>
```

---

## Best Practices

### 1. Testing Strategy
- **Always test on dev first** before promoting to prod
- **Use meaningful test cases** that cover your agent's core functionality
- **Monitor logs and metrics** after each deployment

### 2. Version Management
- **Keep prod on stable versions** - don't rush updates
- **Use semantic versioning** in your deployment notes
- **Keep at least 2-3 versions** available for quick rollback

### 3. Deployment Safety
- **Never deploy directly to prod** without testing
- **Use canary deployments** for high-risk changes
- **Have a rollback plan** before each deployment

### 4. Monitoring and Documentation
- **Monitor after each promotion** to catch issues early
- **Document version changes** in your release notes
- **Track which versions are deployed where**

### 5. Environment Separation
- **Keep dev and prod configurations separate**
- **Use different Cognito pools** for each environment
- **Test authentication flows** on dev before prod

---

## Troubleshooting

### Common Issues

#### Endpoint Not Found
```bash
# Verify agent runtime ID
python scripts/create_endpoint.py --agent-runtime-id <ID> --list
```

#### Version Not Available
```bash
# Check available versions (use AWS Console or CLI)
# Versions are created only through agentcore deploy
```

#### Permission Errors
```bash
# Ensure AWS credentials have bedrock-agentcore permissions
aws sts get-caller-identity
```

### Error Recovery

#### Failed Deployment
1. Check logs: `agentcore status --agent astroAmber --verbose`
2. Rollback endpoints to last known good version
3. Fix issues and redeploy

#### Endpoint Stuck in UPDATING
1. Wait for operation to complete (can take several minutes)
2. Check endpoint status: `python scripts/create_endpoint.py --agent-runtime-id <ID> --get <ENDPOINT>`
3. If stuck, contact AWS support

---

## Example Workflow Timeline

```
Day 1: Initial Setup
├── Deploy v1
├── Create dev → v1
└── Create prod → v1

Day 2: Feature Development
├── Deploy v2 (DEFAULT → v2)
├── Update dev → v2
├── Test on dev
└── Keep prod → v1

Day 3: Production Release
├── Promote prod → v2
└── Monitor production

Day 4: Hotfix
├── Deploy v3 (DEFAULT → v3)
├── Update dev → v3
├── Test hotfix
└── Promote prod → v3
```

This workflow ensures safe, controlled deployments with proper testing and rollback capabilities for your AgentCore applications.
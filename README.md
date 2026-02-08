# AI Deep Research Agent

An intelligent research assistant powered by AWS Bedrock AgentCore and Strands Agent SDK that performs comprehensive web research with real-time streaming capabilities.

## Demo

https://github.com/user-attachments/assets/deep_research.mp4

> Watch the agent in action performing deep research with web search, extraction, and crawling capabilities.

## Overview

This project demonstrates a production-ready AI agent system that combines:
- Advanced web research capabilities (search, extract, crawl)
- Real-time streaming responses
- Professional research formatting with citations
- Modern Next.js frontend with TypeScript
- AWS Bedrock AgentCore deployment

## Architecture

### Backend (Python)
- **Framework**: Strands Agent SDK with AWS Bedrock AgentCore
- **Model**: AWS Bedrock (configurable)
- **Tools**: 
  - Web Search (Tavily API)
  - Web Extract (content extraction)
  - Web Crawl (deep site exploration)
  - Research Formatter (citation and formatting)
- **Deployment**: Containerized with Docker, deployed to AWS

### Frontend (Next.js)
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **UI**: Tailwind CSS with dark theme
- **Features**: 
  - Real-time streaming updates
  - Markdown rendering with syntax highlighting
  - Responsive design
  - Tool execution tracking

## Key Features

- **Intelligent Research Planning**: Agent creates step-by-step research plans
- **Multi-Tool Orchestration**: Automatically selects and chains appropriate tools
- **Real-time Streaming**: Live updates of agent thinking and tool execution
- **Professional Formatting**: Generates well-structured reports with inline citations
- **Source Attribution**: Automatic citation management and source tracking
- **Async Processing**: Non-blocking research execution with progress updates

## Tech Stack

### Backend
- Python 3.11+
- Strands Agent SDK
- AWS Bedrock AgentCore
- Tavily API (web research)
- FastAPI/Starlette (ASGI)
- Docker

### Frontend
- Next.js 15
- TypeScript
- React 19
- Tailwind CSS
- React Markdown
- Syntax Highlighting (highlight.js)

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- AWS Account with Bedrock access
- Tavily API key

### Backend Setup

1. Navigate to the backend directory:
```bash
cd astroAmber
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Configure environment variables in `.env`:
```env
AWS_REGION=eu-west-2
TAVILY_API_KEY=your_tavily_api_key
```

5. Run locally:
```bash
agentcore dev
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment variables in `.env.local`:
```env
AGENT_ID=your_agent_id
AWS_REGION=eu-west-2
```

4. Run development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000)

## Deployment

### Backend Deployment to AWS

1. Configure AWS credentials:
```bash
aws configure
```

2. Deploy to Bedrock AgentCore:
```bash
agentcore deploy
```

3. The agent will be containerized and deployed to AWS with:
   - ECR repository for container images
   - IAM roles for execution
   - CloudWatch for observability
   - Bedrock AgentCore runtime

### Frontend Deployment

Deploy to Vercel:
```bash
vercel deploy
```

Or use the Vercel dashboard for GitHub integration.

## Project Structure

```
.
├── astroAmber/                 # Backend agent
│   ├── src/
│   │   ├── main.py            # Agent entrypoint with tools
│   │   ├── model/             # Model configuration
│   │   └── mcp_client/        # MCP client implementation
│   ├── scripts/               # Deployment scripts
│   ├── .bedrock_agentcore.yaml # Agent configuration
│   └── pyproject.toml         # Python dependencies
│
└── frontend/                   # Next.js frontend
    ├── app/
    │   ├── api/
    │   │   └── invoke-agent/  # Agent invocation API
    │   ├── page.tsx           # Main UI component
    │   └── layout.tsx         # App layout
    └── package.json           # Node dependencies
```

## How It Works

1. **User Query**: User submits a research question through the web interface
2. **Agent Planning**: Agent analyzes the query and creates a research plan
3. **Tool Execution**: Agent orchestrates web search, extraction, and crawling
4. **Streaming Updates**: Real-time progress updates sent to frontend
5. **Formatting**: Research results formatted with citations and structure
6. **Response**: Final formatted research delivered to user

## API Endpoints

### POST /api/invoke-agent
Invokes the research agent with streaming response.

**Request:**
```json
{
  "query": "What are the latest features in AWS Bedrock?"
}
```

**Response:** Server-Sent Events (SSE) stream with:
- Status updates
- Tool execution events
- Thinking content
- Final formatted response

## Environment Variables

### Backend (.env)
- `AWS_REGION`: AWS region for Bedrock
- `TAVILY_API_KEY`: Tavily API key for web research

### Frontend (.env.local)
- `AGENT_ID`: Bedrock AgentCore agent ID
- `AWS_REGION`: AWS region

## Performance

- Average research time: 2-3 minutes
- Supports up to 10 search results per query
- Crawl depth: 2 levels
- Maximum crawl results: 20 pages

## Future Enhancements

- [ ] Multi-language support
- [ ] Research history and caching
- [ ] Export to PDF/Word
- [ ] Custom research templates
- [ ] Collaborative research sessions
- [ ] Integration with more data sources

## License

MIT

## Author

Built for demonstrating advanced AI agent development with AWS Bedrock AgentCore.

## Acknowledgments

- AWS Bedrock AgentCore team
- Strands Agent SDK
- Tavily API
- Next.js team

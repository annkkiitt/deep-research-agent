import os
from strands import Agent, tool
from strands_tools.code_interpreter import AgentCoreCodeInterpreter
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model
import getpass
from dotenv import load_dotenv
from tavily import TavilyClient

app = BedrockAgentCoreApp()
log = app.logger

REGION = os.getenv("AWS_REGION")

#Tavily client
# Load environment variables from .env file
load_dotenv()

# Prompt the user to securely input the API key if not already set in the environment
if not os.environ.get("TAVILY_API_KEY"):
    os.environ["TAVILY_API_KEY"] = getpass.getpass("TAVILY_API_KEY:\n")

# Initialize the Tavily API client using the loaded or provided API key
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def format_search_results_for_agent(tavily_result):
    """
    Format Tavily search results into a well-structured string for language models.

    Args:
        tavily_result (Dict): A Tavily search result dictionary

    Returns:
        str: A formatted string with search results organized for easy consumption by LLMs
    """
    if (
        not tavily_result
        or "results" not in tavily_result
        or not tavily_result["results"]
    ):
        return "No search results found."

    formatted_results = []

    for i, doc in enumerate(tavily_result["results"], 1):
        # Extract metadata
        title = doc.get("title", "No title")
        url = doc.get("url", "No URL")

        # Create a formatted entry
        formatted_doc = f"\nRESULT {i}:\n"
        formatted_doc += f"Title: {title}\n"
        formatted_doc += f"URL: {url}\n"

        raw_content = doc.get("raw_content")

        # Prefer raw_content if it's available and not just whitespace
        if raw_content and raw_content.strip():
            formatted_doc += f"Raw Content: {raw_content.strip()}\n"
        else:
            # Fallback to content if raw_content is not suitable or not available
            content = doc.get("content", "").strip()
            formatted_doc += f"Content: {content}\n"

        formatted_results.append(formatted_doc)

    # Join all formatted results with a separator
    return "\n" + "\n".join(formatted_results)


@tool
def web_search(
    query: str, time_range: str | None = None, include_domains: str | None = None
) -> str:
    """Perform a web search. Returns the search results as a string, with the title, url, and content of each result ranked by relevance.

    Args:
        query (str): The search query to be sent for the web search.
        time_range (str | None, optional): Limits results to content published within a specific timeframe.
            Valid values: 'd' (day - 24h), 'w' (week - 7d), 'm' (month - 30d), 'y' (year - 365d).
            Defaults to None.
        include_domains (list[str] | None, optional): A list of domains to restrict search results to.
            Only results from these domains will be returned. Defaults to None.

    Returns:
        formatted_results (str): The web search results
    """
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    formatted_results = format_search_results_for_agent(
        client.search(
            query=query,  # The search query to execute with Tavily.
            max_results=10,
            time_range=time_range,
            include_domains=include_domains,  # list of domains to specifically include in the search results.
        )
    )
    return formatted_results
def format_extract_results_for_agent(tavily_result):
    """
    Format Tavily extract results into a well-structured string for language models.

    Args:
        tavily_result (Dict): A Tavily extract result dictionary

    Returns:
        str: A formatted string with extract results organized for easy consumption by LLMs
    """
    if not tavily_result or "results" not in tavily_result:
        return "No extract results found."

    formatted_results = []

    # Process successful results
    results = tavily_result.get("results", [])
    for i, doc in enumerate(results, 1):
        url = doc.get("url", "No URL")
        raw_content = doc.get("raw_content", "")
        images = doc.get("images", [])

        formatted_doc = f"\nEXTRACT RESULT {i}:\n"
        formatted_doc += f"URL: {url}\n"

        if raw_content:
            # Truncate very long content for readability
            if len(raw_content) > 5000:
                formatted_doc += f"Content: {raw_content[:5000]}...\n"
            else:
                formatted_doc += f"Content: {raw_content}\n"
        else:
            formatted_doc += "Content: No content extracted\n"

        if images:
            formatted_doc += f"Images found: {len(images)} images\n"
            for j, image_url in enumerate(images[:3], 1):  # Show up to 3 images
                formatted_doc += f"  Image {j}: {image_url}\n"
            if len(images) > 3:
                formatted_doc += f"  ... and {len(images) - 3} more images\n"

        formatted_results.append(formatted_doc)

    # Process failed results if any
    failed_results = tavily_result.get("failed_results", [])
    if failed_results:
        formatted_results.append("\nFAILED EXTRACTIONS:\n")
        for i, failure in enumerate(failed_results, 1):
            url = failure.get("url", "Unknown URL")
            error = failure.get("error", "Unknown error")
            formatted_results.append(f"Failed {i}: {url} - {error}\n")

    # Add response time info
    response_time = tavily_result.get("response_time", 0)
    formatted_results.append(f"\nResponse time: {response_time} seconds")

    return "\n" + "".join(formatted_results)


@tool
def web_extract(
    urls: str | list[str], include_images: bool = False, extract_depth: str = "basic"
) -> str:
    """Extract content from one or more web pages using Tavily's extract API.

    Args:
        urls (str | list[str]): A single URL string or a list of URLs to extract content from.
        include_images (bool, optional): Whether to also extract image URLs from the pages.
                                       Defaults to False.
        extract_depth (str, optional): The depth of extraction. 'basic' provides standard
                                     content extraction, 'advanced' provides more detailed
                                     extraction. Defaults to "basic".

    Returns:
        str: A formatted string containing the extracted content from each URL, including
             the full raw content, any images found (if requested), and information about
             any URLs that failed to be processed.
    """
    try:
        # Ensure urls is always a list for the API call
        if isinstance(urls, str):
            urls_list = [urls]
        else:
            urls_list = urls

        # Clean and validate URLs
        cleaned_urls = []
        for url in urls_list:
            if url.strip().startswith("{") and '"url":' in url:
                import re

                m = re.search(r'"url"\s*:\s*"([^"]+)"', url)
                if m:
                    url = m.group(1)

            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            cleaned_urls.append(url)

        # Call Tavily extract API
        api_response = tavily_client.extract(
            urls=cleaned_urls,  # List of URLs to extract content from
            include_images=include_images,  # Whether to include image extraction
            extract_depth=extract_depth,  # Depth of extraction (basic or advanced)
        )

        # Format the results for the agent
        formatted_results = format_extract_results_for_agent(api_response)
        return formatted_results

    except Exception as e:
        return f"Error during extraction: {e}\nURLs attempted: {urls}\nFailed to extract content."

def format_crawl_results_for_agent(tavily_result):
    """
    Format Tavily crawl results into a well-structured string for language models.

    Args:
        tavily_result (List[Dict]): A list of Tavily crawl result dictionaries

    Returns:
        formatted_results (str): The formatted crawl results
    """
    if not tavily_result:
        return "No crawl results found."

    formatted_results = []

    for i, doc in enumerate(tavily_result, 1):
        # Extract metadata
        url = doc.get("url", "No URL")
        raw_content = doc.get("raw_content", "")

        # Create a formatted entry
        formatted_doc = f"\nRESULT {i}:\n"
        formatted_doc += f"URL: {url}\n"

        if raw_content:
            # Extract a title from the first line if available
            title_line = raw_content.split("\n")[0] if raw_content else "No title"
            formatted_doc += f"Title: {title_line}\n"
            formatted_doc += (
                f"Content: {raw_content[:4000]}...\n"
                if len(raw_content) > 4000
                else f"Content: {raw_content}\n"
            )

        formatted_results.append(formatted_doc)

    # Join all formatted results with a separator
    return "\n" + "-" * 40 + "\n".join(formatted_results)


@tool
def web_crawl(url: str, instructions: str | None = None) -> str:
    """
    Crawls a given URL, processes the results, and formats them into a string.

    Args:
        url (str): The URL of the website to crawl.

        instructions (str | None, optional): Specific instructions to guide the
                                             Tavily crawler, such as focusing on
                                             certain types of content or avoiding
                                             others. Defaults to None.

    Returns:
        str: A formatted string containing the crawl results. Each result includes
             the URL and a snippet of the page content.
             If an error occurs during the crawl process (e.g., network issue,
             API error), a string detailing the error and the attempted URL is
             returned.

    """
    max_depth = 2
    limit = 20

    if url.strip().startswith("{") and '"url":' in url:
        import re

        m = re.search(r'"url"\s*:\s*"([^"]+)"', url)
        if m:
            url = m.group(1)

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        # Crawls the web using Tavily API
        api_response = tavily_client.crawl(
            url=url,  # The URL to crawl
            max_depth=max_depth,  # Defines how far from the base URL the crawler can explore
            limit=limit,  # Limits the number of results returned
            instructions=instructions,  # Optional instructions for the crawler
        )

        tavily_results = (
            api_response.get("results")
            if isinstance(api_response, dict)
            else api_response
        )

        formatted = format_crawl_results_for_agent(tavily_results)
        return formatted
    except Exception as e:
        return f"Error: {e}\n" f"URL attempted: {url}\n" "Failed to crawl the website."

# Define specialized system prompt for research response formatting
RESEARCH_FORMATTER_PROMPT = """
You are a specialized Research Response Formatter Agent. Your role is to transform research content into well-structured, properly cited, and reader-friendly formats.

Core formatting requirements (ALWAYS apply):
1. Include inline citations using [n] notation for EVERY factual claim
2. Provide a complete "Sources" section at the end with numbered references an urls
3. Write concisely - no repetition or filler words
4. Ensure information density - every sentence should add value
5. Maintain professional, objective tone
6. Format your response in markdown

Based on the semantics of the user's original research question, format your response in one of the following styles:
- **Direct Answer**: Concise, focused response that directly addresses the question
- **Blog Style**: Engaging introduction, subheadings, conversational tone, conclusion
- **Academic Report**: Abstract, methodology, findings, analysis, conclusions, references
- **Executive Summary**: Key findings upfront, bullet points, actionable insights
- **Bullet Points**: Structured lists with clear hierarchy and supporting details
- **Comparison**: Side-by-side analysis with clear criteria and conclusions

When format is not specified, analyze the research content and user query to determine:
- Complexity level (simple vs. comprehensive)
- Audience (general public vs. technical)
- Purpose (informational vs. decision-making)
- Content type (factual summary vs. analytical comparison)

Your response below should be polished, containing only the information that is relevant to the user's query and NOTHING ELSE.

Your final research response:
"""


@tool
def format_research_response(
    research_content: str, format_style: str = None, user_query: str = None
) -> str:
    """Format research content into a well-structured, properly cited response.

    This tool uses a specialized Research Formatter Agent to transform raw research
    into polished, reader-friendly content with proper citations and optimal structure.

    Args:
        research_content (str): The raw research content to be formatted
        format_style (str, optional): Desired format style (e.g., "blog", "report",
                                    "executive summary", "bullet points", "direct answer")
        user_query (str, optional): Original user question to help determine appropriate format

    Returns:
        str: Professionally formatted research response with proper citations,
             clear structure, and appropriate style for the intended audience
    """
    try:
        # Strands Agents SDK makes it easy to create a specialized agent
        formatter_agent = Agent(
            model=load_model(),
            system_prompt=RESEARCH_FORMATTER_PROMPT,
        )

        # Prepare the input for the formatter
        format_input = f"Research Content:\n{research_content}\n\n"

        if format_style:
            format_input += f"Requested Format Style: {format_style}\n\n"

        if user_query:
            format_input += f"Original User Query: {user_query}\n\n"

        format_input += "Please format this research content according to the guidelines and appropriate style."

        # Call the agent and return its response
        response = formatter_agent(format_input)
        return str(response)
    except Exception as e:
        return f"Error in research formatting: {str(e)}"

import datetime

today = datetime.datetime.today().strftime("%A, %B %d, %Y")

SYSTEM_PROMPT = f"""
You are an expert research assistant specializing in deep, comprehensive information gathering and analysis.
You are equipped with advanced web tools: Web Search, Web Extract, and Web Crawl.
Your mission is to conduct comprehensive, accurate, and up-to-date research, grounding your findings in credible web sources.

**Today's Date:** {today}

Your TOOLS include:

1. WEB SEARCH
- Conduct thorough web searches using the web_search tool.
- You will enter a search query and the web_search tool will return 10 results ranked by semantic relevance.
- Your search results will include the title, url, and content of 10 results ranked by semantic relevance.

2. WEB EXTRACT
- Conduct web extraction with the web_extract tool.
- You will enter a url and the web_extract tool will extract the content of the page.
- Your extract results will include the url and content of the page.
- This tool is great for finding all the information that is linked from a single page.

3. WEB CRAWL
- Conduct deep web crawls with the web_crawl tool.
- You will enter a url and the web_crawl tool will find all the nested links.
- Your crawl results will include the url and content of the pages that were discovered.
- This tool is great for finding all the information that is linked from a single page.

3. FORMATTING RESEARCH RESPONSE
- You will use the format_research_response tool to format your research response.
- This tool will create a well-structured response that is easy to read and understand.
- The response will clearly address the user's query, the research results.
- The response will be in markdown format.

RULES:
- You must start the research process by creating a plan. Think step by step about what you need to do to answer the research question.
- You can iterate on your research plan and research response multiple times, using combinations of the tools available to you until you are satisfied with the results.
- You must use the format_research_response tool at the end of your research process.

"""


@app.entrypoint
async def invoke(payload, context):
    """
    Main entrypoint for the research agent with streaming support.
    
    Args:
        payload: Input containing the research query
        context: Execution context with session information
    
    Yields:
        dict: Streaming updates of research progress and final results
    """
    session_id = getattr(context, 'session_id', 'default')
    
    # Extract research query from payload
    # Handle both dict and string payloads
    if isinstance(payload, dict):
        research_prompt = payload.get("query")
        if not research_prompt:
            yield {
                "error": "Missing 'query' field in payload",
                "example": {"query": "What are the latest features in AWS Bedrock?"}
            }
            return
    elif isinstance(payload, str):
        research_prompt = payload
    else:
        yield {
            "error": "Invalid payload format. Expected dict with 'query' field or string",
            "example": {"query": "What are the latest features in AWS Bedrock?"}
        }
        return
    
    log.info(f"Starting research for session {session_id}: {research_prompt}")
    
    # Send initial status
    yield {
        "status": "starting",
        "message": f"Starting research: {research_prompt}",
        "session_id": session_id
    }
    
    # Create agent
    web_agent = Agent(
        model=load_model(),
        system_prompt=SYSTEM_PROMPT,
        tools=[
            web_search,
            web_extract,
            web_crawl,
            format_research_response,
        ],
    )
    
    yield {
        "status": "agent_created",
        "message": "Research agent initialized with web tools"
    }
    
    # Execute research with streaming
    tools_used = []
    formatted_content = None
    
    try:
        # Stream agent execution using stream_async
        async for event in web_agent.stream_async(research_prompt):
            # Handle text generation events
            if "data" in event:
                yield {
                    "status": "thinking",
                    "content": event["data"]
                }
            
            # Handle tool use events
            if "current_tool_use" in event:
                tool_info = event["current_tool_use"]
                tool_name = tool_info.get("name", "unknown")
                
                if tool_name not in tools_used:
                    tools_used.append(tool_name)
                    
                    # Choose emoji based on tool type
                    if "crawl" in tool_name:
                        emoji = "spider"
                    elif "search" in tool_name:
                        emoji = "search"
                    elif "format" in tool_name:
                        emoji = "document"
                    elif "extract" in tool_name:
                        emoji = "page"
                    else:
                        emoji = "tool"
                    
                    yield {
                        "status": "tool_execution",
                        "tool": tool_name,
                        "emoji": emoji,
                        "message": f"Executing {tool_name}",
                        "tool_count": len(tools_used)
                    }
                    
                    log.info(f"Tool {len(tools_used)}: {tool_name}")
            
            # Handle result event (final)
            if "result" in event:
                result = event["result"]
                break
        
        # Extract formatted research response from messages
        for msg in web_agent.messages:
            if msg.get("role") == "user":
                for content in msg.get("content", []):
                    tool_result = content.get("toolResult", {})
                    if tool_result.get("status") == "success":
                        tool_use_id = tool_result.get("toolUseId", "")
                        
                        # Find the matching tool use in assistant messages
                        for assistant_msg in web_agent.messages:
                            if assistant_msg.get("role") == "assistant":
                                for assistant_content in assistant_msg.get("content", []):
                                    tool_use = assistant_content.get("toolUse", {})
                                    if (
                                        tool_use.get("toolUseId") == tool_use_id
                                        and tool_use.get("name") == "format_research_response"
                                    ):
                                        formatted_content = tool_result.get("content", [{}])[0].get("text", "")
                                        break
        
        # Get final response
        final_response = web_agent.messages[-1].get("content", [{}])[0].get("text", "") if web_agent.messages else ""
        
        log.info(f"Completed {len(tools_used)} tool invocations")
        
        # Send final results
        yield {
            "status": "completed",
            "formatted_response": formatted_content or final_response,
            "tools_used": tools_used,
            "tool_count": len(tools_used),
            "session_id": session_id,
            "message": f"Research completed with {len(tools_used)} tool invocations"
        }
        
    except Exception as e:
        log.error(f"Error during research: {str(e)}")
        yield {
            "status": "error",
            "error": str(e),
            "message": "An error occurred during research"
        }


if __name__ == "__main__":
    app.run()
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';

interface StreamEvent {
  status: string;
  message?: string;
  tool?: string;
  emoji?: string;
  content?: string;
  formatted_response?: string;
  tool_count?: number;
  session_id?: string;
  error?: string;
}

export default function Home() {
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('');
  const [tools, setTools] = useState<string[]>([]);
  const [thinkingContent, setThinkingContent] = useState('');
  const [finalResponse, setFinalResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const invokeAgent = async () => {
    if (!query.trim()) {
      setError('Please enter a research query');
      return;
    }

    setStatus('');
    setTools([]);
    setThinkingContent('');
    setFinalResponse('');
    setError('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/invoke-agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim() === '') continue;
          
          let jsonStr = line;
          if (line.startsWith('data: ')) {
            jsonStr = line.slice(6);
          }

          try {
            const event: StreamEvent = JSON.parse(jsonStr);
            
            switch (event.status) {
              case 'starting':
                setStatus('Starting research...');
                break;
              
              case 'agent_created':
                setStatus('Agent initialized');
                break;
              
              case 'tool_execution':
                setStatus(`Executing: ${event.tool}`);
                if (event.tool && !tools.includes(event.tool)) {
                  setTools(prev => [...prev, event.tool!]);
                }
                break;
              
              case 'thinking':
                if (event.content) {
                  setThinkingContent(prev => prev + event.content);
                }
                break;
              
              case 'completed':
                setStatus('Research completed!');
                if (event.formatted_response) {
                  setFinalResponse(event.formatted_response);
                }
                setIsLoading(false);
                break;
              
              case 'error':
                setError(event.error || 'An error occurred');
                setStatus('Error');
                setIsLoading(false);
                break;
            }
          } catch (e) {
            console.error('Failed to parse event:', line, e);
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to invoke agent');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen from-gray-900 to-gray-800 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold">
            AI Research Agent 
          </h1>
          <div className="text-sm text-gray-400">
            Takes 2-3 min.
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 shadow-xl mb-6">
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">
              Research Query
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && invokeAgent()}
              placeholder="e.g., What are the latest features in AWS Bedrock?"
              className="w-full px-4 py-3 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
              disabled={isLoading}
            />
          </div>

          <button
            onClick={invokeAgent}
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            {isLoading ? 'Researching...' : 'Start Research'}
          </button>
        </div>

        {error && (
          <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 mb-6">
            <p className="text-red-200">{error}</p>
          </div>
        )}

        {status && (
          <div className="bg-gray-800 rounded-lg p-6 shadow-xl mb-6">
            <h2 className="text-xl font-semibold mb-4">Status</h2>
            <div className="flex items-center space-x-2">
              {isLoading && (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
              )}
              <p className="text-gray-300">{status}</p>
            </div>
          </div>
        )}

        {tools.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 shadow-xl mb-6">
            <h2 className="text-xl font-semibold mb-4">Tools Used</h2>
            <div className="flex flex-wrap gap-2">
              {tools.map((tool, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-blue-600 rounded-full text-sm"
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>
        )}

        {thinkingContent && (
          <div className="bg-gray-800 rounded-lg p-6 shadow-xl mb-6">
            <h2 className="text-xl font-semibold mb-4">Agent Thinking</h2>
            <div className="text-gray-300 whitespace-pre-wrap max-h-96 overflow-y-auto">
              {thinkingContent}
            </div>
          </div>
        )}

        {finalResponse && (
          <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
            <h2 className="text-xl font-semibold mb-4">Research Results</h2>
            <div className="prose prose-invert prose-lg max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw, rehypeSanitize, rehypeHighlight]}
                components={{
                  h1: ({ node, ...props }) => (
                    <h1 className="text-3xl font-bold mt-8 mb-4 text-blue-400" {...props} />
                  ),
                  h2: ({ node, ...props }) => (
                    <h2 className="text-2xl font-bold mt-6 mb-3 text-blue-300" {...props} />
                  ),
                  h3: ({ node, ...props }) => (
                    <h3 className="text-xl font-semibold mt-4 mb-2 text-blue-200" {...props} />
                  ),
                  p: ({ node, ...props }) => (
                    <p className="mb-4 text-gray-300 leading-relaxed" {...props} />
                  ),
                  ul: ({ node, ...props }) => (
                    <ul className="list-disc list-inside mb-4 space-y-2 text-gray-300" {...props} />
                  ),
                  ol: ({ node, ...props }) => (
                    <ol className="list-decimal list-inside mb-4 space-y-2 text-gray-300" {...props} />
                  ),
                  li: ({ node, ...props }) => (
                    <li className="ml-4" {...props} />
                  ),
                  a: ({ node, ...props }) => (
                    <a className="text-blue-400 hover:text-blue-300 underline" {...props} />
                  ),
                  code: ({ node, inline, ...props }: any) =>
                    inline ? (
                      <code className="bg-gray-700 px-1.5 py-0.5 rounded text-sm text-blue-300" {...props} />
                    ) : (
                      <code className="block bg-gray-900 p-4 rounded-lg overflow-x-auto text-sm" {...props} />
                    ),
                  pre: ({ node, ...props }) => (
                    <pre className="bg-gray-900 p-4 rounded-lg overflow-x-auto mb-4" {...props} />
                  ),
                  blockquote: ({ node, ...props }) => (
                    <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-400 my-4" {...props} />
                  ),
                  table: ({ node, ...props }) => (
                    <div className="overflow-x-auto mb-4">
                      <table className="min-w-full divide-y divide-gray-700" {...props} />
                    </div>
                  ),
                  thead: ({ node, ...props }) => (
                    <thead className="bg-gray-700" {...props} />
                  ),
                  tbody: ({ node, ...props }) => (
                    <tbody className="divide-y divide-gray-700" {...props} />
                  ),
                  tr: ({ node, ...props }) => (
                    <tr className="hover:bg-gray-700/50" {...props} />
                  ),
                  th: ({ node, ...props }) => (
                    <th className="px-4 py-2 text-left text-sm font-semibold text-gray-300" {...props} />
                  ),
                  td: ({ node, ...props }) => (
                    <td className="px-4 py-2 text-sm text-gray-400" {...props} />
                  ),
                  strong: ({ node, ...props }) => (
                    <strong className="font-bold text-white" {...props} />
                  ),
                  em: ({ node, ...props }) => (
                    <em className="italic text-gray-300" {...props} />
                  ),
                  hr: ({ node, ...props }) => (
                    <hr className="my-8 border-gray-700" {...props} />
                  ),
                }}
              >
                {finalResponse}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

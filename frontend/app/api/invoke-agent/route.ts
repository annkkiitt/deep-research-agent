/* eslint-disable @typescript-eslint/no-explicit-any */
import { NextResponse } from 'next/server';
import { SignatureV4 } from '@aws-sdk/signature-v4';
import { Sha256 } from '@aws-crypto/sha256-js';
import { HttpRequest } from '@aws-sdk/protocol-http';
import { v4 as uuidv4 } from 'uuid';

const RUNTIME_ARN = 'arn:aws:bedrock-agentcore:eu-west-2:121218444130:runtime/newAgent-BKw0O46tkE';
const USE_LOCAL_AGENT = process.env.USE_LOCAL_AGENT === 'true';
const LOCAL_AGENT_URL = process.env.LOCAL_AGENT_URL || 'http://localhost:8080/invocations';

export async function POST(request: Request) {
  console.log('[Research Agent API] Starting SSE invocation...');
  console.log('[Research Agent API] Mode:', USE_LOCAL_AGENT ? 'LOCAL' : 'AWS');

  try {
    const { query } = await request.json();

    if (!query) {
      console.error('[Research Agent API] Query is required');
      return NextResponse.json(
        { error: 'Query is required' },
        { status: 400 }
      );
    }

    console.log('[Research Agent API] Query:', query);

    // LOCAL MODE - Call local dev server
    if (USE_LOCAL_AGENT) {
      console.log('[Research Agent API] Using local agent at:', LOCAL_AGENT_URL);
      
      const body = JSON.stringify({ query });
      
      const response = await fetch(LOCAL_AGENT_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: body,
      }).catch((fetchError) => {
        console.error('[Research Agent API] Local fetch error:', fetchError);
        throw new Error(`Failed to connect to local agent: ${fetchError.message}`);
      });

      console.log('[Research Agent API] Local response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('[Research Agent API] Local agent error:', errorText);
        throw new Error(`Local agent returned ${response.status}: ${errorText}`);
      }

      console.log('[Research Agent API] Streaming local response back to client...');

      const stream = new ReadableStream({
        async start(controller) {
          const reader = response.body?.getReader();
          if (!reader) {
            console.error('[Research Agent API] No response body');
            controller.close();
            return;
          }

          try {
            let chunkCount = 0;
            while (true) {
              const { done, value } = await reader.read();
              if (done) {
                console.log(`[Research Agent API] Stream complete. Total chunks: ${chunkCount}`);
                break;
              }
              chunkCount++;
              controller.enqueue(value);
            }
          } catch (error) {
            console.error('[Research Agent API] Stream error:', error);
            controller.error(error);
          } finally {
            controller.close();
          }
        },
      });

      return new Response(stream, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      });
    }

    // AWS MODE - Use HTTP with Signature V4 for true streaming
    console.log('[Research Agent API] Runtime ARN:', RUNTIME_ARN);

    const region = RUNTIME_ARN.split(':')[3] || 'eu-west-2';
    console.log('[Research Agent API] Extracted region:', region);

    const accessKeyId = process.env.AWS_ACCESS_KEY_ID;
    const secretAccessKey = process.env.AWS_SECRET_ACCESS_KEY;
    const sessionToken = process.env.AWS_SESSION_TOKEN;

    console.log('[Research Agent API] Credentials check:');
    console.log('  - Access Key ID:', accessKeyId ? `${accessKeyId.substring(0, 8)}...` : 'NOT SET');
    console.log('  - Secret Access Key:', secretAccessKey ? `${secretAccessKey.substring(0, 8)}...` : 'NOT SET');
    console.log('  - Session Token:', sessionToken ? 'SET' : 'NOT SET');

    if (!accessKeyId || !secretAccessKey) {
      console.error('[Research Agent API] AWS credentials not found');
      return NextResponse.json(
        { error: 'AWS credentials not found in environment variables' },
        { status: 500 }
      );
    }

    // Generate session ID
    const sessionId = `session-${uuidv4()}-${Date.now()}`;
    console.log('[Research Agent API] Session ID:', sessionId);

    // Construct the HTTP endpoint URL
    // The ARN already includes the endpoint qualifier, so just encode it
    const host = `bedrock-agentcore.${region}.amazonaws.com`;
    const encodedArn = encodeURIComponent(RUNTIME_ARN);
    const path = `/runtimes/${encodedArn}/invocations`;

    console.log('[Research Agent API] Constructing request:');
    console.log('  - Host:', host);
    console.log('  - Path:', path);
    console.log('  - Full URL:', `https://${host}${path}`);

    const body = JSON.stringify({ query });

    // Create HTTP request for signing
    const httpRequest = new HttpRequest({
      method: 'POST',
      protocol: 'https:',
      hostname: host,
      path: path,
      headers: {
        'Content-Type': 'application/json',
        'host': host,
        'x-amz-bedrock-agentcore-session-id': sessionId,
      },
      body: body,
    });

    console.log('[Research Agent API] Signing request...');

    // Sign the request with SigV4
    const signer = new SignatureV4({
      credentials: {
        accessKeyId,
        secretAccessKey,
        ...(sessionToken && { sessionToken }),
      },
      region,
      service: 'bedrock-agentcore',
      sha256: Sha256,
    });

    const signedRequest = await signer.sign(httpRequest);
    console.log('[Research Agent API] Request signed successfully');

    // Make the HTTP request with streaming
    const agentUrl = `https://${host}${path}`;
    console.log('[Research Agent API] Invoking agent at:', agentUrl);

    const response = await fetch(agentUrl, {
      method: 'POST',
      headers: {
        ...signedRequest.headers,
        'Content-Type': 'application/json',
      } as HeadersInit,
      body: body,
    }).catch((fetchError) => {
      console.error('[Research Agent API] Fetch error:', fetchError);
      throw fetchError;
    });

    console.log('[Research Agent API] Response status:', response.status);
    console.log('[Research Agent API] Response headers:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[Research Agent API] AgentCore error:', errorText);
      throw new Error(`AgentCore returned ${response.status}: ${errorText}`);
    }

    console.log('[Research Agent API] Streaming response to client...');

    // Stream the response directly
    const stream = new ReadableStream({
      async start(controller) {
        const reader = response.body?.getReader();
        if (!reader) {
          console.error('[Research Agent API] No response body');
          controller.close();
          return;
        }

        try {
          let chunkCount = 0;
          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              console.log(`[Research Agent API] Stream complete. Total chunks: ${chunkCount}`);
              break;
            }
            chunkCount++;
            
            // Log first few chunks for debugging
            if (chunkCount <= 3) {
              const text = new TextDecoder().decode(value);
              console.log(`[Research Agent API] Chunk ${chunkCount}:`, text.substring(0, 100));
            }
            
            controller.enqueue(value);
          }
        } catch (error) {
          console.error('[Research Agent API] Stream error:', error);
          controller.error(error);
        } finally {
          controller.close();
        }
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error('[Research Agent API] Error:');
    console.error('  - Error type:', error?.constructor?.name);
    console.error('  - Error message:', error instanceof Error ? error.message : 'Unknown error');
    console.error('  - Error cause:', (error as any)?.cause);
    console.error('  - Stack trace:', error instanceof Error ? error.stack : 'No stack trace');

    return NextResponse.json(
      {
        error: 'Failed to invoke agent',
        details: error instanceof Error ? error.message : 'Unknown error',
        cause: (error as any)?.cause?.message || 'No cause available',
        type: error?.constructor?.name || 'UnknownError',
      },
      { status: 500 }
    );
  }
}

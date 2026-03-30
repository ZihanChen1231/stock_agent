# Stock Analysis Agent (RAG + ReAct + MCP)

## Goal

Build a local AI agent system that: - Uses ReAct reasoning loop - Uses
RAG for knowledge retrieval - Uses MCP-style tool interface - Optimizes
token usage

## Architecture

User → Agent Service → ReAct Loop → Tools → RAG → Output

## Components

-   FastAPI service
-   Local vector DB (Chroma/FAISS)
-   MCP tools (price/news) service
-   LLM (OpenAI or local)

## Key Features

-   Multi-step reasoning (ReAct)
-   Top-k retrieval (RAG)
-   Token optimization
-   Structured prompts

## Tasks

1.  Build FastAPI skeleton
2.  Implement tool layer
3.  Add RAG pipeline
4.  Add ReAct loop
5.  Optimize token usage

## Insight

This is a simplified Lynx-style agent system for stock analysis.

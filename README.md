# CodeSaarthiAI
A Structurally Aware code understanding Agent for Onboarding and training.
# Cloud Backend --- Code Intelligence Platform

## Overview

This repository contains the cloud backend powering a **code
intelligence and agent-assisted developer system**. The platform ingests
repositories, builds semantic and structural understanding of codebases,
and enables AI agents to retrieve architectural knowledge only when
required.

The backend transforms raw source code into a hybrid knowledge system
combining:

-   **Semantic search (vector embeddings)**
-   **Structural reasoning (knowledge graph)**

The system is designed to run both as:

-   **Distributed cloud infrastructure**, or
-   **Instance-based deployments** with reduced components.

------------------------------------------------------------------------

## System Components

The backend consists of three primary services:

1.  **Ingestion Service** --- Repository parsing, dependency extraction,
    embeddings, and graph construction\
2.  **Semantic Service (Optional)** --- LLM-powered description
    generation pipeline\
3.  **Lambda Backend** --- Agent utilities and retrieval orchestration

------------------------------------------------------------------------

## Optional path:

Workers → Queue → Semantic Service (vLLM + DeepSeekCoder)

------------------------------------------------------------------------

## 1. Ingestion Service

### Purpose

The ingestion pipeline converts a repository into structured
machine-understandable knowledge.

### Core Responsibilities

-   Parallelized repository extraction
-   Repository cloning
-   Static code analysis using **Tree-sitter**
-   Dependency and relationship discovery
-   Semantic metadata extraction
-   Embedding generation
-   Knowledge graph construction

### Processing Pipeline

#### Repository Cloning

The service first clones the target repository locally before analysis
begins.

#### Code Parsing

Tree-sitter is used to parse source files and extract:

-   Imports
-   Function and method calls
-   Class relationships
-   Module dependencies

#### Semantic Extraction

Code units are converted into structured descriptions capturing
functional intent.

#### Embedding Generation

Extracted code entities are embedded and stored in **OpenSearch** for
semantic retrieval.

#### Graph Construction

A dependency graph is simultaneously created in **Amazon Neptune**:

-   Nodes represent code entities
-   Edges represent relationships such as imports, calls, and
    dependencies

### Output

-   Vector embeddings for semantic search
-   Knowledge graph for structural reasoning

------------------------------------------------------------------------

## 2. Semantic Service (Optional)

### Purpose

Provides large-scale semantic understanding using an LLM inference
service.

> **Note:**\
> This service is **optional** and primarily intended for distributed or
> high-throughput deployments.\
> Instance-based setups can bypass this service and generate
> descriptions directly during ingestion.

### Runtime

-   Runs on **vLLM**
-   Uses **DeepSeekCoder** for code reasoning and description generation

### Architecture

The service operates using a queue-driven workflow:

Workers → Processing Queue → LLM Processor → Structured Descriptions

### Workflow

1.  Ingestion workers push parsing outputs to a queue.
2.  The semantic service consumes jobs asynchronously.
3.  DeepSeekCoder generates:
    -   Code summaries
    -   Functional descriptions
    -   Architectural explanations
4.  Results are returned to the ingestion pipeline.

### Why Optional?

For smaller deployments:

-   Running a dedicated LLM service may be unnecessary.
-   Descriptions can be generated inline.
-   Reduces infrastructure complexity.

For large-scale ingestion:

-   Prevents GPU overload
-   Enables centralized inference
-   Improves throughput and scalability

------------------------------------------------------------------------

## 3. Lambda Backend (Agent Utilities)

### Purpose

Acts as the execution layer for AI agents interacting with indexed
repositories.

### Agent Model

-   Uses **Claude** as the reasoning agent.
-   Retrieval is performed only when additional context is required.

### Responsibilities

-   Agent helper utilities
-   Conditional retrieval orchestration
-   Graph and semantic queries
-   Session-aware execution logic

### Retrieval Strategy

The agent dynamically decides when to retrieve knowledge:

-   Query **Neptune** for structural relationships
-   Query vector index for semantic similarity
-   Merge retrieved context into reasoning flow

This approach improves:

-   Accuracy
-   Context efficiency
-   Architectural awareness
-   Reduced hallucinations

------------------------------------------------------------------------

## Deployment Modes

### Distributed Cloud Mode

Recommended for large repositories or multi-user environments.

Includes:

-   Dedicated semantic service
-   Queue-based processing
-   Scalable ingestion workers

### Instance-Based Mode

Lightweight deployment for experimentation or smaller workloads.

Includes:

-   Ingestion service
-   Lambda backend
-   Inline semantic generation (Semantic Service optional)

------------------------------------------------------------------------

## Technology Stack

  Component        Technology
  ---------------- -----------------------------
  Parsing          Tree-sitter
  LLM Runtime      vLLM
  Code Model       DeepSeekCoder
  Agent Model      Claude
  Vector Storage   OpenSearch
  Graph Database   Amazon Neptune
  Compute          AWS Lambda
  Processing       Worker + Queue Architecture

------------------------------------------------------------------------

## High-Level Data Flow

1.  Repository submitted for ingestion
2.  Code parsed and dependencies extracted
3.  (Optional) Semantic descriptions generated via LLM service
4.  Embeddings stored in vector index
5.  Relationships stored in Neptune graph
6.  Agent retrieves knowledge dynamically during queries

------------------------------------------------------------------------

## Design Principles

-   Hybrid knowledge representation (graph + vector)
-   Retrieval-on-demand agent architecture
-   Parallel-first ingestion pipeline
-   Scalable LLM processing
-   Modular deployment flexibility

------------------------------------------------------------------------

## Future Improvements

-   Incremental repository indexing
-   Graph-aware reasoning prompts
-   Multi-language parsing expansion
-   Streaming ingestion support
-   Agent planning over dependency graphs

------------------------------------------------------------------------


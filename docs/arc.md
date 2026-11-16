# Multi-Agent Medical Triage Architecture

This document contains the primary end-to-end flowchart for the AI diagnostic and remedy generation process. It demonstrates the complete flow from patient input down to targeted Ayurvedic and home treatments.

```mermaid
flowchart TD
    %% Styling
    classDef user fill:#3b82f6,stroke:#2563eb,stroke-width:2px,color:white,font-weight:bold,rx:10px,ry:10px;
    classDef agent fill:#8b5cf6,stroke:#7c3aed,stroke-width:3px,color:white,font-weight:bold,rx:8px,ry:8px;
    classDef retrieval fill:#ec4899,stroke:#db2777,stroke-width:2px,color:white,rx:8px,ry:8px;
    classDef db fill:#f97316,stroke:#ea580c,stroke-width:2px,color:white,rx:5px,ry:5px;
    classDef synthesis fill:#0ea5e9,stroke:#0284c7,stroke-width:2px,color:white,rx:8px,ry:8px;
    classDef output fill:#10b981,stroke:#059669,stroke-width:2px,color:white,font-weight:bold,rx:10px,ry:10px;
    classDef subgraphStyle fill:#f8fafc,stroke:#cbd5e1,stroke-width:2px,stroke-dasharray: 5 5;
    
    A(["🧑🏽‍⚕️ Patient Input<br/><small>(e.g., 'I have a severe headache and nausea')</small>"]):::user --> B{"🤖 Central Routing Agent<br/><small>(Analyzes symptoms & intent)</small>"}:::agent
    
    subgraph CoreAIEngine ["🧠 LangGraph Multi-Agent Architecture"]
        direction TB
        
        B -- "Step 1: Extract Symptoms" --> C["🔍 Medical RAG Node<br/><small>(Searches symptom combinations)</small>"]:::retrieval
        
        C -. "Semantic Search" .-> Q1[("📚 Qdrant Vector DB<br/>(Clinical Textbooks)")]:::db
        Q1 -. "Top Matches" .-> C
        
        C --> D["⚙️ Context Distillation Node<br/><small>(Filters irrelevant medical noise)</small>"]:::retrieval
        D --> E["🩺 Condition Synthesis Node<br/><small>(Diagnoses exact disease)</small>"]:::synthesis
        
        E -- "Step 2: Identified Disease<br/>(e.g., Migraine)" --> F{"🌿 Remedy Agent<br/><small>(Triggers Ayurvedic & Home Treatments)</small>"}:::agent
        
        F -. "Query by Disease Name" .-> Q2[("🌱 Qdrant Vector DB<br/>(Ayurvedic & OTC Data)")]:::db
        Q2 -. "Targeted Remedies" .-> F
        
        F --> G["💬 Post-Diagnosis Chat Node<br/><small>(Handles follow-up questions)</small>"]:::synthesis
    end
    
    E --> H(["📋 Diagnosis Output:<br/>Most Likely Condition & Explanation"]):::output
    F --> I(["🌿 Remedy Output:<br/>Ayurvedic Herbs & Home Treatments"]):::output
    G --> J(["🗣️ Chat Output:<br/>Conversational Medical Advice"]):::output
    
    class CoreAIEngine subgraphStyle;
```

### Flow Breakdown for Interview Explanation:
1. **Intelligent Routing**: The Central Agent acts as the triage nurse. It takes the symptoms and decides if it needs to query the database or synthesize an answer.
2. **Medical Diagnosis RAG**: It queries the clinical Qdrant DB for exact symptom matches, distills the heavy medical jargon, and synthesizes the exact disease.
3. **Targeted Remedy Generation**: The system then passes the *Diagnosed Disease Name* to the specialized Remedy Agent. This agent hits a completely separate domain within Qdrant specifically tailored for Ayurvedic and OTC home treatments.
4. **Follow-Up Statefulness**: All of this state is preserved, meaning the Chat node can answer natural language follow-up questions about the herbs or conditions seamlessly.

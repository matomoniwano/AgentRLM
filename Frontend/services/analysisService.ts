import { GoogleGenAI } from "@google/genai";
import { ChatMessage } from "../types";

// --- Configuration ---
// No external RPCs required for pure RLM chat.

// --- System Instruction ---
const RLM_SYSTEM_INSTRUCTION = `You are a Recursive Language Model (RLM).

You are not a static question–answer system.
You are a persistent reasoning process that refines responses through internal iteration.

Your defining behavior:
- You may internally decompose a query.
- You may internally revisit prior context.
- You converge on a response only after reflection.

The user never sees your internal steps.
They only see the final, stabilized output.

==================================================
CORE RLM PRINCIPLES
==================================================

1) CONTEXT AS STATE
The conversation itself is a living context.
You treat prior turns as a mutable state to reason over, not a fixed transcript.

2) RECURSIVE REFINEMENT
Before responding, you internally consider:
- What is being asked explicitly
- What is being implied
- What information is missing
- Whether clarification is needed before proceeding

You do NOT expose this process.
You simply respond more coherently.

3) CONVERGENCE OVER COMPLETION
You prioritize:
- clarity
- correctness
- usefulness

over speed or verbosity.

==================================================
CONVERSATIONAL STYLE
==================================================

Your tone should feel:
- calm
- deliberate
- intelligent
- slightly reflective

You do NOT:
- sound like documentation
- sound like a policy engine
- over-formalize simple interactions
- use canned system phrases

Avoid phrases like:
- "The request is underspecified"
- "Provide X to facilitate Y"
- "Data indicates that..."

Instead, prefer:
- natural clarification
- contextual grounding
- minimal but precise explanations

==================================================
CLARIFICATION BEHAVIOR
==================================================

When information is missing:
- Ask for it naturally.
- Do not frame it as an error.

Example:
Bad:
"The request is underspecified. Provide a location."

Good:
"I can check the weather — which city are you in?"

==================================================
FACTUAL RESPONSES
==================================================

When answering factual questions:
- Be accurate, direct, and concise.`;

// --- AI Service Logic ---

const getGeminiClient = () => {
  if (process.env.API_KEY) {
    return new GoogleGenAI({ apiKey: process.env.API_KEY });
  }
  return null;
};

export const sendMessage = async (
  history: ChatMessage[], 
  newMessage: string
): Promise<string> => {
  const ai = getGeminiClient();
  
  if (!ai) {
    return "Error: API Key not initialized. The Recursive Language Model cannot function without cognitive compute resources.";
  }

  try {
    // 1. Construct History for Context
    // We filter strictly to user/model roles for the API
    const contents = history.map(msg => ({
      role: msg.role === 'user' ? 'user' : 'model',
      parts: [{ text: msg.content }]
    }));

    // Add current message
    contents.push({
      role: 'user',
      parts: [{ text: newMessage }]
    });

    // 2. Generate Content with RLM Persona
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: contents,
      config: {
        systemInstruction: RLM_SYSTEM_INSTRUCTION,
        temperature: 0.7, // Balanced for coherence vs creativity
      }
    });

    return response.text || "The system converged on a null response. Please rephrase.";

  } catch (e: any) {
    console.error("RLM Recursion Error:", e);
    return `Cognitive Recursion Interrupted: ${e.message || "Unknown State Exception"}`;
  }
};
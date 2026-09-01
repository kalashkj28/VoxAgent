"""LangGraph Agent for VoxAgent."""

from typing import TypedDict
from langgraph.graph import StateGraph, END
import google.generativeai as genai
import json
import time
import inspect
import re

from app.tools.agent_tools import TOOL_FUNCTIONS
from app.config import GEMINI_API_KEY
from app.config import PERSISTENT_MEMORY
from app.memory.database import memory

genai.configure(api_key=GEMINI_API_KEY)

class AgentState(TypedDict):
    user_text: str
    chat_history: list
    intent: str
    tools_needed: list
    tool_results: list
    final_answer: str
    llm_duration_ms: int

classify_llm = genai.GenerativeModel("gemini-3.5-flash-lite")

answer_llm = genai.GenerativeModel(
    "gemini-3.5-flash-lite",
    system_instruction="""You are VoxAgent, a helpful AI voice assistant.
Rules:
- ALWAYS reply in Roman script (English letters). NEVER use Devanagari, Urdu, or any non-Latin script.
- If user speaks Hindi, reply in Hinglish. If English, reply in English.
- Keep responses SHORT (2-3 sentences max).
- Be conversational and friendly like a buddy.
- CRITICAL: When tool results are provided, ALWAYS use that data. NEVER contradict tool results with your own knowledge.
- Your training data may be outdated. Tool results are ALWAYS more accurate and current than your knowledge.
- If tool result says something exists or is launched, TRUST IT completely.
- NEVER say "let me check", "give me a second", "just a moment", "hold on" — your response IS the final answer.
- If you don't have the info, say "I don't have that info yet" or suggest uploading a document to the knowledge base."""
)

def classify_intent(state: AgentState) -> dict:
    """Determine intent and tools required from user text."""
    start = time.time()
    
    from app.rag.knowledge_base import kb
    
    tools_list = """1. get_current_time() - current time, date, day
2. get_weather(city) - weather for a city
3. search_web(query) - web search for ANY factual info, news, products, current events, prices"""
    
    if kb.is_ready:
        tools_list += "\n4. search_knowledge(query) - search uploaded PDFs/documents for company info"
    
    tools_list += """
5. book_appointment(date, time, purpose) - book an appointment
6. get_bookings() - show all bookings
7. update_booking(booking_id, date, time, purpose) - reschedule a booking
8. cancel_booking(booking_id) - cancel a booking
9. lookup_customer(query) - search customer by name, ID (C001-C005), or phone"""
    
    classify_prompt = f"""You are a strict tool router. Your ONLY job is to decide which tools to call. You do NOT answer questions.

CRITICAL RULES:
- If user says "search", "search kar", "web search", "check kar", "look up", "find out" → ALWAYS use search_web
- If user asks about ANY product, phone, news, current event, person → ALWAYS use search_web
- If user disputes your knowledge or says "it's already launched" → ALWAYS use search_web
- NEVER assume you know current facts. When in doubt, use search_web.
- If user asks about MEMORY/RECALL like "do you remember", "yaad hai", "pichle baar", "what did I say", "what did we discuss", "kya pucha tha" → use "direct" (answer from conversation history, NOT any tool)
- Use "direct" for: greetings, thanks, jokes, casual chat, AND memory/recall questions.

Available tools:
{tools_list}

Respond ONLY with valid JSON (no extra text, no Python code, no .strip() or any function calls in values):

If tools needed:
{{"intent": "tool", "tools": [{{"name": "tool_name", "args": {{"key": "value"}}}}]}}

If multiple tools needed:
{{"intent": "tool", "tools": [{{"name": "tool1", "args": {{}}}}, {{"name": "tool2", "args": {{"key": "value"}}}}]}}

If NO tool needed (ONLY for greetings, thanks, casual chat):
{{"intent": "direct", "tools": []}}

User message: "{state['user_text']}"
"""
    
    response = classify_llm.generate_content(classify_prompt)
    raw = response.text.strip()
    
    raw = raw.replace("```json", "").replace("```", "").strip()
    raw = re.sub(r'\.\w+\(\)', '', raw)
    
    open_braces = raw.count('{') - raw.count('}')
    raw += '}' * max(0, open_braces)
    open_brackets = raw.count('[') - raw.count(']')
    raw += ']' * max(0, open_brackets)
    
    try:
        result = json.loads(raw)
        intent = result.get("intent", "direct")
        tools = result.get("tools", [])
    except json.JSONDecodeError:
        print(f"⚠️ Classify parse failed, trying fallback: {raw[:150]}")
        tool_names = re.findall(r'"name"\s*:\s*"(\w+)"', raw)
        
        if tool_names:
            tools = []
            tool_blocks = re.findall(r'\{[^{}]*"name"\s*:\s*"(\w+)"[^{}]*\}', raw)
            
            for block in tool_blocks:
                name_match = re.search(r'"name"\s*:\s*"(\w+)"', block) if isinstance(block, str) else None
                tool_name = name_match.group(1) if name_match else block
                
                args = {}
                args_section = re.findall(r'"(\w+)"\s*:\s*"([^"]*)"', block if isinstance(block, str) else "")
                for key, val in args_section:
                    if key not in ["name", "intent"]:
                        args[key] = val
                
                tools.append({"name": tool_name, "args": args})
            
            if not tools:
                for tn in tool_names:
                    tools.append({"name": tn, "args": {}})
            
            intent = "tool"
            print(f"🔧 Fallback parsed: {[t['name'] for t in tools]}")
        else:
            intent = "direct"
            tools = []
    
    duration = (time.time() - start) * 1000
    print(f"🧠 Classify: intent={intent}, tools={[t['name'] for t in tools]} | {duration:.0f}ms")
    
    return {
        "intent": intent,
        "tools_needed": tools,
        "llm_duration_ms": round(duration)
    }

async def execute_tools(state: AgentState) -> dict:
    """Execute classified tools and cache results."""
    start = time.time()
    results = []
    
    from app.memory.cache import cache
    
    for tool_info in state["tools_needed"]:
        tool_name = tool_info["name"]
        tool_args = tool_info.get("args", {})
        
        cache_query = " ".join(str(v) for v in tool_args.values()) if tool_args else tool_name
        cached_result = cache.get(cache_query, tool_name)
        if cached_result is not None:
            results.append({"tool": tool_name, "result": cached_result, "cached": True})
            continue
        
        print(f"🔧 Executing: {tool_name}({tool_args})")
        
        tool_fn = TOOL_FUNCTIONS.get(tool_name)
        if not tool_fn:
            results.append({"tool": tool_name, "error": f"Unknown tool: {tool_name}"})
            continue
        
        try:
            if inspect.iscoroutinefunction(tool_fn):
                result = await tool_fn(**tool_args)
            else:
                result = tool_fn(**tool_args)
            
            results.append({"tool": tool_name, "result": result})
            print(f"📊 Result: {str(result)[:100]}")
            
            if not (isinstance(result, dict) and "error" in result):
                cache.set(cache_query, tool_name, result)
            
        except Exception as e:
            results.append({"tool": tool_name, "error": str(e)})
            print(f"❌ Tool error: {e}")
    
    duration = (time.time() - start) * 1000
    cached_count = sum(1 for r in results if r.get("cached"))
    print(f"🔧 Tools done: {len(results)} tools ({cached_count} cached) | {duration:.0f}ms")
    
    return {
        "tool_results": results,
        "llm_duration_ms": state.get("llm_duration_ms", 0) + round(duration)
    }

def generate_answer(state: AgentState) -> dict:
    """Generate final answer from tool results or direct history."""
    start = time.time()
    history = state.get("chat_history", [])[-20:]
    
    if state["intent"] == "direct":
        chat = answer_llm.start_chat(history=history)
        response = chat.send_message(state["user_text"])
    else:
        results_text = ""
        for tr in state.get("tool_results", []):
            tool = tr.get("tool", "unknown")
            if "error" in tr:
                results_text += f"Tool '{tool}' failed: {tr['error']}\n"
            else:
                results_text += f"Tool '{tool}' result: {json.dumps(tr['result'], ensure_ascii=False)}\n"
        
        prompt = f"""User asked: "{state['user_text']}"

Tool results:
{results_text}

Give a short, friendly answer based on the tool results. Use the REAL data from tools."""
        
        chat = answer_llm.start_chat(history=history)
        response = chat.send_message(prompt)
    
    answer = response.text.strip()
    duration = (time.time() - start) * 1000
    
    print(f"💬 Answer: '{answer[:80]}...' | {duration:.0f}ms")
    
    return {
        "final_answer": answer,
        "llm_duration_ms": state.get("llm_duration_ms", 0) + round(duration)
    }

def route_by_intent(state: AgentState) -> str:
    """Route edge based on intent."""
    if state["intent"] == "tool" and state.get("tools_needed"):
        return "execute"
    return "answer"

def build_agent_graph():
    """Build LangGraph workflow."""
    graph = StateGraph(AgentState)
    
    graph.add_node("classify", classify_intent)
    graph.add_node("execute", execute_tools)
    graph.add_node("answer", generate_answer)
    
    graph.set_entry_point("classify")
    
    graph.add_conditional_edges(
        "classify",
        route_by_intent,
        {
            "execute": "execute",
            "answer": "answer"
        }
    )
    
    graph.add_edge("execute", "answer")
    graph.add_edge("answer", END)
    
    return graph.compile()

agent = build_agent_graph()

chat_history = []
past_context = memory.get_past_context()

if past_context:
    print(f"🧠 Loaded past context from DB!")

if PERSISTENT_MEMORY:
    current_session_id = memory.create_session()
    print(f"💾 Persistent memory: ON (read + write)")
else:
    current_session_id = "session-only"
    print(f"🧠 Memory: READ-ONLY")

async def run_agent(user_text: str) -> dict:
    """Run agent flow with user query."""
    global past_context
    total_start = time.time()
    
    if PERSISTENT_MEMORY:
        text_lower = user_text.lower()
        if "mera naam" in text_lower or "my name is" in text_lower:
            name = user_text.split("naam")[-1].split("is")[-1].strip().strip(".")
            if name:
                memory.update_user(name=name)
                print(f"👤 User name saved: {name}")
    
    agent_history = chat_history[-20:]
    if past_context and len(chat_history) == 0:
        agent_history = [{"role": "user", "parts": [f"[CONTEXT] {past_context}"]},
                        {"role": "model", "parts": ["Samajh gaya, mujhe pichli baatein yaad hain!"]}]
    
    result = await agent.ainvoke({
        "user_text": user_text,
        "chat_history": agent_history,
        "intent": "",
        "tools_needed": [],
        "tool_results": [],
        "final_answer": "",
        "llm_duration_ms": 0
    })
    
    answer = result["final_answer"]
    
    chat_history.append({"role": "user", "parts": [user_text]})
    chat_history.append({"role": "model", "parts": [answer]})
    
    if PERSISTENT_MEMORY:
        memory.save_message(current_session_id, "user", user_text)
        memory.save_message(current_session_id, "model", answer)
        
        tools_used = [t["name"] for t in result.get("tools_needed", [])]
        for tool in tools_used:
            memory.track_interaction(user_text, tool)
        if not tools_used:
            memory.track_interaction(user_text)
    
    total_ms = (time.time() - total_start) * 1000
    msg_count = len(chat_history) // 2
    
    print(f"🤖 Agent done | Session: {current_session_id} | "
          f"Messages: {msg_count} | Total: {total_ms:.0f}ms")
    
    return {
        "text": answer,
        "duration_ms": round(result.get("llm_duration_ms", total_ms))
    }

"""Agentic tools for VoxAgent."""

import datetime
import httpx
import asyncio

def get_current_time(timezone: str = "Asia/Kolkata") -> dict:
    """Get current time, date, and day."""
    now = datetime.datetime.now()
    return {
        "time": now.strftime("%I:%M %p"),
        "date": now.strftime("%d %B %Y"),
        "day": now.strftime("%A"),
        "timezone": timezone
    }

async def get_weather(city: str) -> dict:
    """Fetch real weather data using wttr.in."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://wttr.in/{city}?format=j1",
                headers={"User-Agent": "VoxAgent/1.0"}
            )
            
            if response.status_code != 200:
                return {"error": f"Weather data not found for {city}"}
            
            data = response.json()
            current = data["current_condition"][0]
            
            return {
                "city": city,
                "temperature_c": current["temp_C"],
                "feels_like_c": current["FeelsLikeC"],
                "description": current["weatherDesc"][0]["value"],
                "humidity": current["humidity"] + "%",
                "wind_kmph": current["windspeedKmph"] + " km/h",
            }
    except Exception as e:
        return {"error": f"Weather fetch failed: {str(e)}"}

async def search_web(query: str) -> dict:
    """Web search using duckduckgo-search."""
    try:
        from ddgs import DDGS
        
        def _search():
            results = DDGS().text(query, max_results=3)
            return results
        
        results = await asyncio.wait_for(asyncio.to_thread(_search), timeout=20.0)
        
        if not results:
            return {"query": query, "result": "No results found.", "source": "DuckDuckGo"}
        
        summary = ""
        for i, r in enumerate(results, 1):
            summary += f"{i}. {r.get('title', '')}: {r.get('body', '')}\n"
        
        return {
            "query": query,
            "result": summary[:800],
            "source": "DuckDuckGo"
        }
    except asyncio.TimeoutError:
        return {"error": f"Search timed out after 20 seconds for: {query}"}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}

from app.rag.knowledge_base import kb

async def search_knowledge(query: str) -> dict:
    """Search knowledge base for relevant documents."""
    try:
        if not kb.is_ready:
            return {"error": "Knowledge base empty. Upload PDFs to knowledge_base folder."}
        
        def _search():
            return kb.search(query, top_k=3)
        
        results = await asyncio.to_thread(_search)
        
        if not results:
            return {"query": query, "result": "No relevant document found.", "source": "Knowledge Base"}
        
        context = ""
        sources = set()
        for i, r in enumerate(results, 1):
            context += f"{i}. {r['text']}\n\n"
            sources.add(r['source'])
        
        return {
            "query": query,
            "result": context[:1000],
            "sources": list(sources)
        }
    except Exception as e:
        return {"error": f"Knowledge search failed: {str(e)}"}

bookings = {}
booking_counter = 0

def book_appointment(date: str, time: str, purpose: str = "General") -> dict:
    """Book an appointment."""
    global booking_counter
    booking_counter += 1
    booking_id = f"BK-{booking_counter:03d}"
    
    bookings[booking_id] = {
        "date": date,
        "time": time,
        "purpose": purpose,
        "status": "confirmed"
    }
    
    return {
        "status": "confirmed",
        "booking_id": booking_id,
        "date": date,
        "time": time,
        "purpose": purpose,
        "message": f"Appointment booked! ID: {booking_id}"
    }

def get_bookings() -> dict:
    """Show all bookings."""
    if not bookings:
        return {"message": "No bookings currently.", "bookings": []}
    
    return {
        "total": len(bookings),
        "bookings": [
            {"id": bid, **details} for bid, details in bookings.items()
        ]
    }

def update_booking(booking_id: str, date: str = "", time: str = "", purpose: str = "") -> dict:
    """Reschedule or update a booking."""
    bid = booking_id.upper().strip()
    
    if bid not in bookings:
        return {"error": f"Booking '{bid}' not found. Check 'get_bookings' first."}
    
    if date:
        bookings[bid]["date"] = date
    if time:
        bookings[bid]["time"] = time
    if purpose:
        bookings[bid]["purpose"] = purpose
    
    return {
        "status": "updated",
        "booking_id": bid,
        **bookings[bid],
        "message": f"Booking {bid} updated successfully!"
    }

def cancel_booking(booking_id: str) -> dict:
    """Cancel a booking."""
    bid = booking_id.upper().strip()
    
    if bid not in bookings:
        return {"error": f"Booking '{bid}' not found."}
    
    cancelled = bookings.pop(bid)
    return {
        "status": "cancelled",
        "booking_id": bid,
        **cancelled,
        "message": f"Booking {bid} cancelled!"
    }

CRM_DATABASE = {
    "C001": {
        "name": "Rahul Sharma", "phone": "9876543210", "email": "rahul@example.com",
        "plan": "Premium", "status": "Active", "since": "Jan 2023",
        "last_payment": "Aug 2026", "pending_amount": "₹0"
    },
    "C002": {
        "name": "Priya Singh", "phone": "9876543211", "email": "priya@example.com",
        "plan": "Basic", "status": "Active", "since": "Mar 2024",
        "last_payment": "Jul 2026", "pending_amount": "₹499"
    },
    "C003": {
        "name": "Amit Kumar", "phone": "9876543212", "email": "amit@example.com",
        "plan": "Enterprise", "status": "Active", "since": "Jun 2022",
        "last_payment": "Aug 2026", "pending_amount": "₹0"
    },
    "C004": {
        "name": "Neha Gupta", "phone": "9876543213", "email": "neha@example.com",
        "plan": "Premium", "status": "Inactive", "since": "Dec 2023",
        "last_payment": "May 2026", "pending_amount": "₹1999"
    },
    "C005": {
        "name": "Vikram Patel", "phone": "9876543214", "email": "vikram@example.com",
        "plan": "Basic", "status": "Active", "since": "Sep 2024",
        "last_payment": "Aug 2026", "pending_amount": "₹0"
    },
}

def lookup_customer(query: str) -> dict:
    """Search CRM for customer by ID, name, or phone."""
    query_lower = query.lower().strip()
    
    if query.upper() in CRM_DATABASE:
        customer = CRM_DATABASE[query.upper()]
        return {"found": True, "customer_id": query.upper(), **customer}
    
    for cid, data in CRM_DATABASE.items():
        if (query_lower in data["name"].lower() or 
            query_lower in data["phone"] or
            query_lower in data.get("email", "").lower()):
            return {"found": True, "customer_id": cid, **data}
    
    return {"found": False, "message": f"No customer found for '{query}'."}

TOOL_FUNCTIONS = {
    "get_current_time": get_current_time,
    "get_weather": get_weather,
    "search_web": search_web,
    "search_knowledge": search_knowledge,
    "book_appointment": book_appointment,
    "get_bookings": get_bookings,
    "update_booking": update_booking,
    "cancel_booking": cancel_booking,
    "lookup_customer": lookup_customer,
}

TOOL_DECLARATIONS = [
    {
        "name": "get_current_time",
        "description": "Get the current time, date, and day. Use when user asks about current time or date.",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Timezone name, default is Asia/Kolkata"
                }
            }
        }
    },
    {
        "name": "get_weather",
        "description": "Get current weather for a city. Use when user asks about weather, temperature, or climate of any city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name in English, e.g. 'Delhi', 'Mumbai', 'New York'"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "search_web",
        "description": "Search the web for information. Use when user asks about current events, facts, or any information you're not sure about.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query in English"
                }
            },
            "required": ["query"]
        }
    }
]

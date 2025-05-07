import os
import json
import asyncio
from datetime import datetime, timedelta
import gradio as gr
from typing import Dict, List, Any, Optional
import pandas as pd
import google.generativeai as genai
# from genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
load_dotenv()


# Initialize Gemini client
def initialize_genai_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-pro-exp-03-25")



# Configure MCP server parameters
def get_mcp_server_params():
    serp_api_key = os.getenv("SERPER_API_KEY")
    if not serp_api_key:
        raise ValueError("SERP_API_KEY environment variable not set")
    
    return StdioServerParameters(
        command="mcp-flight-search",
        args=["--connection_type", "stdio"],
        env={"SERP_API_KEY": serp_api_key},
    )

# Process flight data into a more user-friendly format
def process_flight_data(flight_data: Dict) -> Dict:
    """Transform the raw flight data into a more structured format for display"""
    processed_data = {
        "search_info": {},
        "flights": []
    }
    
    # Extract search information
    if "searchInfo" in flight_data:
        processed_data["search_info"] = {
            "origin": flight_data["searchInfo"].get("origin", "N/A"),
            "destination": flight_data["searchInfo"].get("destination", "N/A"),
            "departure_date": flight_data["searchInfo"].get("departureDate", "N/A"),
            "return_date": flight_data["searchInfo"].get("returnDate", ""),
            "passenger_count": flight_data["searchInfo"].get("passengerCount", 1),
            "cabin_class": flight_data["searchInfo"].get("cabinClass", "Economy"),
        }
    
    # Extract flight options
    if "flightOptions" in flight_data:
        for option in flight_data["flightOptions"]:
            flight_info = {
                "price": option.get("price", {}).get("formatted", "N/A"),
                "duration": option.get("duration", "N/A"),
                "airlines": [leg.get("airline", "N/A") for leg in option.get("legs", [])],
                "departure": option.get("legs", [{}])[0].get("departure", {}).get("time", "N/A"),
                "arrival": option.get("legs", [{}])[-1].get("arrival", {}).get("time", "N/A"),
                "stops": len(option.get("legs", [])) - 1,
                "legs": []
            }
            
            # Process individual legs/segments
            for leg in option.get("legs", []):
                leg_info = {
                    "airline": leg.get("airline", "N/A"),
                    "flight_number": leg.get("flightNumber", "N/A"),
                    "from": f"{leg.get('departure', {}).get('airport', {}).get('code', 'N/A')}",
                    "to": f"{leg.get('arrival', {}).get('airport', {}).get('code', 'N/A')}",
                    "departure_time": leg.get("departure", {}).get("time", "N/A"),
                    "arrival_time": leg.get("arrival", {}).get("time", "N/A"),
                    "duration": leg.get("duration", "N/A"),
                }
                flight_info["legs"].append(leg_info)
                
            processed_data["flights"].append(flight_info)
    
    return processed_data

# Create a DataFrame from flight data for tabular display
def create_flights_dataframe(processed_data: Dict) -> pd.DataFrame:
    """Convert processed flight data to a pandas DataFrame for display"""
    if not processed_data.get("flights"):
        return pd.DataFrame()
    
    flights_data = []
    for flight in processed_data["flights"]:
        airlines = ", ".join(set(flight["airlines"]))
        flights_data.append({
            "Price": flight["price"],
            "Duration": flight["duration"],
            "Airlines": airlines,
            "Departure": flight["departure"],
            "Arrival": flight["arrival"],
            "Stops": flight["stops"],
        })
    
    return pd.DataFrame(flights_data)

# Main flight search function
async def search_flights(
    prompt: str, 
    from_city: str = "", 
    to_city: str = "", 
    departure_date: str = "", 
    return_date: str = "", 
    passengers: int = 1, 
    cabin_class: str = "Economy"
) -> Dict:
    """Search for flights using Gemini and MCP flight search tool"""
    client = initialize_genai_client()
    server_params = get_mcp_server_params()
    
    # Construct a natural language prompt if individual fields are provided
    if from_city and to_city and departure_date:
        return_info = f" returning {return_date}" if return_date else ""
        passenger_info = f" for {passengers} passenger{'s' if passengers > 1 else ''}"
        cabin_info = f" in {cabin_class} class" if cabin_class != "Economy" else ""
        
        prompt = f"Find flights from {from_city} to {to_city} on {departure_date}{return_info}{passenger_info}{cabin_info}"
    
    # Run the search
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Get available tools from MCP
            mcp_tools = await session.list_tools()
            tools = [
                types.Tool(
                    function_declarations=[
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": {
                                k: v
                                for k, v in tool.inputSchema.items()
                                if k not in ["additionalProperties", "$schema"]
                            },
                        }
                    ]
                )
                for tool in mcp_tools.tools
            ]
            
            # Generate content with Gemini
            response = client.models.generate_content(
                model="gemini-2.5-pro-exp-03-25",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    tools=tools,
                ),
            )
            
            # Check if a function call was generated
            if response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call
                result = await session.call_tool(
                    function_call.name, arguments=dict(function_call.args)
                )
                
                try:
                    flight_data = json.loads(result.content[0].text)
                    processed_data = process_flight_data(flight_data)
                    return {
                        "status": "success",
                        "raw_data": flight_data,
                        "processed_data": processed_data,
                        "flights_df": create_flights_dataframe(processed_data)
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "message": "Failed to parse flight search results",
                        "details": result.content[0].text if result.content else "No content"
                    }
                except (IndexError, AttributeError, KeyError) as e:
                    return {
                        "status": "error",
                        "message": f"Error processing results: {str(e)}",
                        "details": str(result) if result else "No result"
                    }
            else:
                return {
                    "status": "error",
                    "message": "No flight search was performed",
                    "details": response.text if hasattr(response, "text") else "No response text"
                }

# Function to handle Gradio interface submission
def handle_search(
    search_type, natural_prompt, from_city, to_city, 
    departure_date, return_date, passengers, cabin_class
):
    """Handle the flight search form submission from Gradio"""
    if search_type == "Natural Language":
        prompt = natural_prompt
        from_city = to_city = departure_date = return_date = ""
        passengers = 1
        cabin_class = "Economy"
    else:
        prompt = ""
    
    # Run the async flight search function
    result = asyncio.run(search_flights(
        prompt, from_city, to_city, departure_date, return_date, 
        passengers, cabin_class
    ))
    
    if result["status"] == "success":
        processed_data = result["processed_data"]
        flights_df = result["flights_df"]
        
        # Create search info summary
        search_info = processed_data["search_info"]
        search_summary = f"**Flight Search Results**\n\n"
        search_summary += f"From: {search_info['origin']} To: {search_info['destination']}\n"
        search_summary += f"Date: {search_info['departure_date']}"
        if search_info['return_date']:
            search_summary += f" - {search_info['return_date']}"
        search_summary += f"\nPassengers: {search_info['passenger_count']}, Class: {search_info['cabin_class']}"
        
        # Create detailed flight information (for when a specific flight is selected)
        if flights_df.empty:
            detailed_info = "No flights found matching your criteria."
        else:
            detailed_info = "Select a flight from the table to see details."
        
        return search_summary, flights_df, detailed_info
    else:
        error_message = f"**Error: {result['message']}**\n\n{result['details']}"
        return error_message, pd.DataFrame(), ""

# Function to display detailed flight information when a row is selected
def show_flight_details(evt: gr.SelectData, results):
    """Show detailed information for a selected flight"""
    if results["status"] != "success" or not results["processed_data"]["flights"]:
        return "No flight details available"
    
    selected_index = evt.index[0]
    if selected_index >= len(results["processed_data"]["flights"]):
        return "Invalid selection"
    
    flight = results["processed_data"]["flights"][selected_index]
    
    details = f"## Flight Details\n\n"
    details += f"**Price:** {flight['price']}\n"
    details += f"**Total Duration:** {flight['duration']}\n"
    details += f"**Stops:** {flight['stops']}\n\n"
    
    details += "### Itinerary\n\n"
    for i, leg in enumerate(flight["legs"]):
        details += f"**Segment {i+1}:** {leg['airline']} {leg['flight_number']}\n"
        details += f"From: {leg['from']} at {leg['departure_time']}\n"
        details += f"To: {leg['to']} at {leg['arrival_time']}\n"
        details += f"Duration: {leg['duration']}\n\n"
    
    return details

# Generate some default dates for the UI
def get_default_dates():
    today = datetime.now()
    departure = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    return_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")
    return departure, return_date

# Create the Gradio interface
def create_interface():
    departure_default, return_default = get_default_dates()
    
    with gr.Blocks(title="Flight Search App", theme="soft") as app:
        gr.Markdown("# ✈️ Flight Search App")
        gr.Markdown("Search for flights using natural language or structured inputs")
        
        # Store the raw results for flight detail selection
        results_state = gr.State({})
        
        with gr.Tabs():
            with gr.TabItem("Search"):
                with gr.Row():
                    search_type = gr.Radio(
                        ["Natural Language", "Structured Form"], 
                        label="Search Type", 
                        value="Structured Form"
                    )
                
                # Natural Language Search
                with gr.Column(visible=False) as natural_search:
                    natural_prompt = gr.Textbox(
                        label="Describe your flight search",
                        placeholder="e.g., Find flights from New York to London next Friday returning Sunday"
                    )
                
                # Structured Form Search
                with gr.Column() as structured_search:
                    with gr.Row():
                        from_city = gr.Textbox(label="From", placeholder="City or airport code")
                        to_city = gr.Textbox(label="To", placeholder="City or airport code")
                    
                    with gr.Row():
                        departure_date = gr.Textbox(
                            label="Departure Date (YYYY-MM-DD)", 
                            placeholder="YYYY-MM-DD",
                            value=departure_default
                        )
                        return_date = gr.Textbox(
                            label="Return Date (optional)", 
                            placeholder="YYYY-MM-DD",
                            value=""
                        )
                    
                    with gr.Row():
                        passengers = gr.Slider(
                            minimum=1, maximum=9, value=1, step=1,
                            label="Passengers"
                        )
                        cabin_class = gr.Dropdown(
                            ["Economy", "Premium Economy", "Business", "First"], 
                            label="Cabin Class",
                            value="Economy"
                        )
                
                search_button = gr.Button("Search Flights", variant="primary")
            
            with gr.TabItem("About"):
                gr.Markdown("""
                ## About This App
                
                This Flight Search application uses Google's Gemini AI to process natural language queries 
                about flight searches. It connects to a flight search service to find real flight options 
                based on your criteria.
                
                ### How to Use
                
                1. Choose between Natural Language or Structured Form search
                2. Enter your search criteria
                3. Click "Search Flights"
                4. View the results in the table
                5. Click on a flight to see detailed information
                
                ### Requirements
                
                This application requires:
                - GEMINI_API_KEY environment variable
                - SERP_API_KEY environment variable
                - mcp-flight-search tool installed
                """)
        
        # Toggle visibility based on search type selection
        search_type.change(
            fn=lambda x: [x == "Natural Language", x == "Structured Form"],
            inputs=search_type,
            outputs=[natural_search, structured_search]
        )
        
        # Results section
        with gr.Row():
            with gr.Column():
                search_summary = gr.Markdown("Search results will appear here")
            
        with gr.Row():
            flights_table = gr.DataFrame(
                headers=["Price", "Duration", "Airlines", "Departure", "Arrival", "Stops"],
                interactive=False,
                wrap=True
            )
        
        with gr.Row():
            flight_details = gr.Markdown("Select a flight to see details")
        
        # Set up the search button click event
        search_button.click(
            fn=handle_search,
            inputs=[
                search_type, natural_prompt, from_city, to_city,
                departure_date, return_date, passengers, cabin_class
            ],
            outputs=[search_summary, flights_table, flight_details],
            api_name="search"
        )
        
        # Handle flight selection in the table
        flights_table.select(
            fn=show_flight_details,
            inputs=[results_state],
            outputs=flight_details
        )
    
    return app

# Main function to run the app
def main():
    app = create_interface()
    app.launch(share=True, inbrowser=True)

if __name__ == "__main__":
    main()
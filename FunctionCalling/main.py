import gradio as gr
import ollama
import requests
import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from processing import parse_function_call, google_search, process_message


# Create Gradio Interface
with gr.Blocks(css="footer {visibility: hidden}") as demo:
    gr.Markdown("""
    # 🤖 ✨ Gemma3 - Function Calling Demo 🔍 🌐
    This is a demo of the function calling capabilities of Gemma3. You can ask questions and get answers from the model.
    """)
    
    chatbot = gr.Chatbot(
        height=500,
        show_label=False,
        avatar_images=(None, "https://api.dicebear.com/7.x/bottts/svg?seed=gemma"),
        type="messages"
    )
    
    with gr.Row():
        msg = gr.Textbox(
            scale=5,
            show_label=False,
            placeholder="Ask me anything...",
            container=False
        )
        submit_btn = gr.Button("Send", scale=1)
    
    with gr.Row():
        clear_btn = gr.Button("Clear Chat")
    

    # Set up event handlers
    msg.submit(
        process_message,
        [msg, chatbot],
        [chatbot],
    )
    
    submit_btn.click(
        process_message,
        [msg, chatbot],
        [chatbot],
    )
    
    clear_btn.click(
        lambda: [],
        None,
        chatbot,
        queue=False
    )
    
    # Clear textbox after sending message
    msg.submit(lambda: "", None, msg)
    submit_btn.click(lambda: "", None, msg)

if __name__ == "__main__":
    demo.launch(inbrowser=True, share=True) 
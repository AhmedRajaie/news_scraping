import anthropic
import os

# Initialize the client
client = anthropic.Anthropic(
    api_key=""
)

# System prompt
SYSTEM_PROMPT = "You are a helpful AI assistant. Be concise and friendly."

# Store conversation history
conversation_history = []

print("Claude Chatbot (type 'quit' to exit)\n")

while True:
    # Get user input
    user_input = input("You: ")
    
    if user_input.lower() == 'quit':
        print("Goodbye!")
        break
    
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_input
    })
    
    # Call Claude API
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=conversation_history
    )
    
    # Get assistant's response
    assistant_message = response.content[0].text
    
    # Add assistant message to history
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })
    
    # Display response
    print(f"\nClaude: {assistant_message}\n")

    
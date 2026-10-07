import asyncio
import websockets
import json
import sys

async def simulate_call(elder_id):
    uri = f"ws://localhost:8000/api/v1/voice/ws?elder_id={elder_id}"
    print(f"Connecting to {uri}")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Listening for AI greeting...")
            
            # 1. Listen for greeting
            greeting = await websocket.recv()
            msg = json.loads(greeting)
            print(f"AI: {msg.get('text')}")
            
            # 2. Simulate speech event (VAD)
            print("\nSimulating VAD (barge-in)...")
            await websocket.send(json.dumps({"event": "speech_started"}))
            
            # 3. Send speech
            speech = "I need help! It is an emergency."
            print(f"User: {speech}")
            await websocket.send(json.dumps({"event": "speech_recognized", "text": speech}))
            
            # 4. Listen for AI response
            response = await websocket.recv()
            msg = json.loads(response)
            print(f"AI: {msg.get('text')}")
            
            print("\nSimulation complete!")
            
    except ConnectionRefusedError:
        print("Error: Could not connect to the server. Is the FastAPI backend running?")
    except websockets.exceptions.InvalidURI:
        print("Error: Invalid URI.")

if __name__ == "__main__":
    elder_id = 1
    if len(sys.argv) > 1:
        elder_id = sys.argv[1]
    asyncio.run(simulate_call(elder_id))

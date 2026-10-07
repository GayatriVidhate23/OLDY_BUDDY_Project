import asyncio
import json
import base64
from fastapi import WebSocket
from app.services import process_ai_conversation
from app.schemas import ConversationRequest
from app.models import VoiceCall
from app.database import async_sessionmaker, engine
from sqlalchemy.ext.asyncio import AsyncSession
import datetime

class VoiceSession:
    def __init__(self, websocket: WebSocket, elder_id: int = None, db: AsyncSession = None):
        self.ws = websocket
        self.elder_id = elder_id
        self.is_listening = True
        self.call_record = None
        self.db = db

    async def start(self):
        await self.ws.accept()
        
        # Initialize call record
        if self.db:
            self.call_record = VoiceCall(elder_id=self.elder_id or 1, call_type="INBOUND", status="IN_PROGRESS")
            self.db.add(self.call_record)
            await self.db.commit()
            await self.db.refresh(self.call_record)

        await self.say("Hello there! I am your Oldy Buddy assistant. How are you feeling today?")
        
        try:
            while True:
                data = await self.ws.receive_text()
                msg = json.loads(data)
                await self.handle_message(msg)
        except Exception as e:
            print(f"Voice session ended: {e}")
            if self.call_record and self.db:
                self.call_record.status = "COMPLETED"
                self.call_record.ended_at = datetime.datetime.now(datetime.timezone.utc)
                self.db.add(self.call_record)
                await self.db.commit()

    async def handle_message(self, msg: dict):
        event = msg.get("event")
        if event == "media":
            # Receive u-law audio chunk (base64 encoded)
            # In a real app, send to STT provider like Sarvam
            pass
        elif event == "speech_started": # VAD
            self.barge_in()
        elif event == "speech_recognized":
            text = msg.get("text", "")
            await self.process_speech(text)
        elif event == "dtmf":
            digit = msg.get("digit")
            print(f"DTMF received: {digit}")

    def barge_in(self):
        # Stop current TTS playback
        self.is_listening = True

    async def say(self, text: str):
        # Uses Sarvam TTS (Fake)
        await self.ws.send_text(json.dumps({"event": "say", "text": text}))

    async def process_speech(self, text: str):
        req = ConversationRequest(prompt=text, elder_id=self.elder_id)
        res = await process_ai_conversation(req)
        
        # If it was an emergency, the service would have logged an SOS activity.
        await self.say(res.reply)

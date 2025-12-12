from pydantic import BaseModel
from typing import List, Optional, Any

class NewNote(BaseModel):
    id: str
    title: str
    content: str
    email: str
    createdAt: str
    addCalendar: bool

class EventItem(BaseModel):
    id: str
    title: str
    description: str
    email: str
    date: str
    time: str
    color: str
    eventDateTime: str
    notificationSent: bool

class RecommendRequest(BaseModel):
    userEmail: str
    newNote: NewNote
    allEventsInMonth: List[EventItem]

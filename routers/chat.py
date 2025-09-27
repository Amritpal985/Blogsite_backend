from fastapi import APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from models import Users,ChatMessages,Follows
from database import SessionLocal
from typing import Annotated
from services import auth_services
from schemas import ChatRequest

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(auth_services.get_current_user)]
bcrypt_context = auth_services.bcrypt_context
authenticate_user = auth_services.authenticate_user


# router for chat where user follow each other and chat
router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

# Helper 
def are_mutual_followers(db:Session,user_id:int,user_2:int):
    follow_1 = db.query(Follows).filter(
        Follows.follower_id == user_id,
        Follows.following_id == user_2
    ).first()
    follow_2 = db.query(Follows).filter(
        Follows.follower_id == user_2,
        Follows.following_id == user_id
    ).first()
    return follow_1 is not None and follow_2 is not None

# REST API to send a message

@router.post("/send",status_code=status.HTTP_201_CREATED)
def send_message(chat_request: ChatRequest,current_user: user_dependency,db: db_dependency):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        if are_mutual_followers(db,current_user["id"],chat_request.receiver_id) is False:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only message users who follow you back.")
        if chat_request.receiver_id == current_user["id"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot send message to yourself.")
        new_message = ChatMessages(
            sender_id=current_user["id"],
            receiver_id=chat_request.receiver_id,
            message=chat_request.message
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        return {"message": "Message sent successfully", "data": new_message.id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# REST API to get chat history with a specific user
@router.get("/history/{with_user_id}",status_code=status.HTTP_200_OK)
def get_chat_history(with_user_id:int,current_user: user_dependency,db: db_dependency):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        if are_mutual_followers(db,current_user["id"],with_user_id) is False:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view messages of users who follow you back.")
        messages = db.query(ChatMessages).filter(
            ((ChatMessages.sender_id == current_user["id"]) & (ChatMessages.receiver_id == with_user_id)) |
            ((ChatMessages.sender_id == with_user_id) & (ChatMessages.receiver_id == current_user["id"]))
        ).order_by(ChatMessages.timestamp).all()
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# api to mark messages as read
@router.post("/mark_read/{message_id}",status_code=status.HTTP_200_OK)
def mark_message_as_read(message_id:int,current_user: user_dependency,db: db_dependency):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        message = db.query(ChatMessages).filter(ChatMessages.id == message_id, ChatMessages.receiver_id == current_user["id"]).first()
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")
        message.is_read = 1  # Mark as read
        db.commit()
        return {"message": "Message marked as read."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# web-socket for real time chat 
active_connections : dict[str,WebSocket] = {}

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket,user_id:str,db: db_dependency):
    await websocket.accept()
    active_connections[user_id] = websocket
    try:
        while True:
            data = await websocket.receive_json()
            receiver_id = str(data.get("receiver_id"))
            message_text = data.get("message")
            sender_id = int(user_id)
            if not are_mutual_followers(db,sender_id,int(receiver_id)):
                await websocket.send_json({"error": "You can only message users who follow you back."})
                continue
            if receiver_id == user_id:
                await websocket.send_json({"error": "You cannot send message to yourself."})
                continue
            new_message = ChatMessages(
                sender_id=sender_id,
                receiver_id=int(receiver_id),
                message=message_text
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            if receiver_id in active_connections:
                await active_connections[receiver_id].send_json({
                    "sender_id": sender_id,
                    "message": message_text,
                    "timestamp": new_message.timestamp.isoformat()
                })
            await websocket.send_json({
                "message": "Message sent successfully",
                "data": {
                    "id": new_message.id,
                    "timestamp": new_message.timestamp.isoformat()
                }
            })                                          
    except WebSocketDisconnect:
        active_connections.pop(user_id, None)

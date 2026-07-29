from flask import request
from flask_socketio import join_room, leave_room, emit
from app.extensions import socketio

# In-memory dictionary to track user connections per quiz: {quiz_id: set(session_id)}
quiz_active_takers = {}

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    # Remove from tracking lists if disconnected abruptly
    for quiz_id, sids in list(quiz_active_takers.items()):
        if request.sid in sids:
            sids.remove(request.sid)
            emit('active_takers_update', {'count': len(sids)}, to=f"quiz_{quiz_id}")

@socketio.on('join_quiz')
def handle_join_quiz(data):
    quiz_id = str(data.get('quiz_id'))
    if not quiz_id:
        return
        
    room = f"quiz_{quiz_id}"
    join_room(room)
    
    if quiz_id not in quiz_active_takers:
        quiz_active_takers[quiz_id] = set()
    
    quiz_active_takers[quiz_id].add(request.sid)
    
    # Broadcast current taker count to the room
    emit('active_takers_update', {'count': len(quiz_active_takers[quiz_id])}, to=room)

@socketio.on('leave_quiz')
def handle_leave_quiz(data):
    quiz_id = str(data.get('quiz_id'))
    if not quiz_id:
        return
        
    room = f"quiz_{quiz_id}"
    leave_room(room)
    
    if quiz_id in quiz_active_takers and request.sid in quiz_active_takers[quiz_id]:
        quiz_active_takers[quiz_id].remove(request.sid)
        
    # Broadcast updated taker count to the room
    emit('active_takers_update', {'count': len(quiz_active_takers.get(quiz_id, []))}, to=room)

@socketio.on('trigger_leaderboard_refresh')
def handle_leaderboard_refresh(data):
    quiz_id = str(data.get('quiz_id'))
    if not quiz_id:
        return
    # Broadcast to all listeners of this quiz leaderboard
    emit('leaderboard_refresh', {}, to=f"leaderboard_{quiz_id}", include_self=True)

@socketio.on('join_leaderboard')
def handle_join_leaderboard(data):
    quiz_id = str(data.get('quiz_id'))
    if quiz_id:
        join_room(f"leaderboard_{quiz_id}")

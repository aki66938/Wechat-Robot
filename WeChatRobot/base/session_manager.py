# -*- coding: utf-8 -*-

class UserSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.state = "INITIAL"
        self.data = {}

    def update_state(self, new_state):
        self.state = new_state

    def store_data(self, key, value):
        self.data[key] = value

    def retrieve_data(self, key):
        return self.data.get(key, None)

class SessionManager:
    sessions = {}

    @staticmethod
    def get_session(user_id):
        if user_id not in SessionManager.sessions:
            SessionManager.sessions[user_id] = UserSession(user_id)
        return SessionManager.sessions[user_id]

    @staticmethod
    def end_session(user_id):
        if user_id in SessionManager.sessions:
            del SessionManager.sessions[user_id]
import streamlit as st

# User Database
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "student": {"password": "student123", "role": "user"}
}

def login():
    st.sidebar.title("🔐 Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = user["role"]
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")

def logout():
    """Clears all session data and logs out user."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
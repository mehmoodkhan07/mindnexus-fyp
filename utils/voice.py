import speech_recognition as sr
import pyttsx3
import threading
import streamlit as st

# Global tracker for the speaking state
engine_instance = None

def speak(text):
    global engine_instance
    
    def worker(t):
        global engine_instance
        try:
            engine_instance = pyttsx3.init()
            engine_instance.setProperty("rate", 165)
            engine_instance.say(t)
            engine_instance.runAndWait()
        except:
            pass
        finally:
            engine_instance = None
            if "speaking" in st.session_state:
                st.session_state.speaking = False

    if engine_instance:
        stop_speak()
    else:
        st.session_state.speaking = True
        threading.Thread(target=worker, args=(text,), daemon=True).start()

def stop_speak():
    global engine_instance
    if engine_instance:
        try:
            engine_instance.stop()
            engine_instance = None
            st.session_state.speaking = False
        except:
            pass

def listen():
    r = sr.Recognizer()
    try:
        # Check if a microphone is actually available to PyAudio
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=5)
            return r.recognize_google(audio)
    except OSError:
        # This catches the "No Default Input Device" error
        st.error("🎤 Microphone not found. Please check your system sound settings.")
        return None
    except Exception as e:
        # Catches other errors like timeouts or Google API issues
        return None
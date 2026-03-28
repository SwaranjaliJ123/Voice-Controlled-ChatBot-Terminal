import tkinter as tk
from tkinter import scrolledtext, messagebox
import speech_recognition as sr
import pyttsx3
import paho.mqtt.client as mqtt
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import serial


# === Ollama LLM Setup ===
template = """
Answer the question below.

Here is the conversation history: {context}

Question: {question}

Answer:
"""
model = OllamaLLM(model="llama3.2")
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model
context = ""

# === Text-to-Speech ===
engine = pyttsx3.init()

# === MQTT Setup ===
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC = "chatbot/responses"
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# === Serial Setup ===
try:
    ser = serial.Serial('COM9', 9600, timeout=1)  # Replace with correct COM port
except Exception as e:
    ser = None
    print(f"Serial port error: {e}")

# === Speech to Text ===
def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        chat_window.insert(tk.END, "Listening...\n")
        chat_window.yview(tk.END)
        audio = recognizer.listen(source)
    
    try:
        user_input = recognizer.recognize_google(audio).lower()
        entry.delete(0, tk.END)
        entry.insert(0, user_input)
        get_response(user_input)
    except sr.UnknownValueError:
        messagebox.showerror("Error", "Sorry, I could not understand your speech.")
    except sr.RequestError:
        messagebox.showerror("Error", "Sorry, my speech service is down.")

# === Get Bot Response ===
def get_response(user_input):
    global context
    user_input = user_input.strip().lower()

    try:
        result = chain.invoke({"context": context, "question": user_input})
        response = str(result)
        context += f"\nUser: {user_input}\nAI: {response}"
    except Exception as e:
        response = f"Sorry, I encountered an error: {e}"

    chat_window.config(state=tk.NORMAL)
    chat_window.insert(tk.END, f"You: {user_input}\n", 'user')
    chat_window.insert(tk.END, f"ChatBot: {response}\n\n", 'bot')
    chat_window.config(state=tk.DISABLED)
    chat_window.yview(tk.END)

    engine.say(response)
    engine.runAndWait()
    mqtt_client.publish(MQTT_TOPIC, response)

    # === Send to NodeMCU (scrollable text) ===
    if ser and ser.is_open:
        try:
            ser.write((response + "\n").encode())
        except Exception as e:
            print(f"Serial send failed: {e}")

# === Login Function ===
def login():
    username = username_entry.get()
    password = password_entry.get()
    if username == "admin" and password == "admin":
        login_window.destroy()
        root.deiconify()
    else:
        messagebox.showerror("Login Failed", "Invalid username or password")

# === Login Window ===
login_window = tk.Tk()
login_window.title("Login")
login_window.geometry("400x300")
login_window.configure(bg='orange')

tk.Label(login_window, text="Login", font=("Helvetica", 24, "bold"), bg='orange').pack(pady=20)
tk.Label(login_window, text="Username", bg='orange').pack()
username_entry = tk.Entry(login_window)
username_entry.pack()
tk.Label(login_window, text="Password", bg='orange').pack()
password_entry = tk.Entry(login_window, show="*")
password_entry.pack()
tk.Button(login_window, text="Login", command=login).pack(pady=20)

# === Main Window ===
root = tk.Tk()
root.title("Voice ChatBot")
root.geometry("1200x600")
root.configure(bg='orange')
root.withdraw()

left_frame = tk.Frame(root, bg='orange')
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

chat_window = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Helvetica", 14), bg='#FFFFFF')
chat_window.pack(fill=tk.BOTH, expand=True)
chat_window.tag_configure('user', foreground='blue')
chat_window.tag_configure('bot', foreground='black')

input_frame = tk.Frame(left_frame)
input_frame.pack(fill=tk.X, pady=10)
entry = tk.Entry(input_frame, font=("Helvetica", 14))
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

speech_button = tk.Button(input_frame, text="Speak", command=speech_to_text)
speech_button.pack(side=tk.LEFT)

login_window.mainloop()
root.mainloop()
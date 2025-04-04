import threading
from tkinter import *
import tkinter as tk
from tkinter import ttk
from gtts import gTTS
from mutagen.mp3 import MP3
from playsound3 import playsound
import os

class ttsManager:
    def __init__(self, root):
        self.root = root
        self.TTSDuration = 0
        self.filename = 'TypingTTS.mp3'
        self.typingText = "This is example text."

    # Function to get the typing text
    def getTypingText(self):
        return self.typingText

    # Function to get the duration of the tts
    def getTTSDuration(self):
        return self.TTSDuration

    # Function to delete tts file
    def deleteTTSFile(self):
        os.remove(self.filename)

    # Make tts file from input text, and update tts duration
    def TTSGenerate(self, input_text):
        tts_file = gTTS(input_text, lang='en')
        tts_file.save(self.filename)
        file_generated = MP3(self.filename)
        self.TTSDuration = file_generated.info.length

    # Play TTS using threading to avoid blocking
    def playTTS(self):
        threading.Thread(target=playsound, args=(self.filename,), daemon=True).start()


class ProgressBarManager:
    def __init__(self, root, tts_manager):
        self.root = root
        self.tts_manager = tts_manager
        self.update_interval = 100  # Update every 100 milliseconds
        self.progress_value = 0  # Track the progress bar value
        self.timer_id = None  # Track the timer ID
        self.is_paused = True

        # Create the progress bar
        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.grid(row=0, column=1, pady=10, sticky="s")
        self.progress_bar["maximum"] = 100  # Set a maximum value for the progress bar

        # Update audio duration using getTTSDuration()
        self.update_audio_duration()

    def update_audio_duration(self):
        self.audio_duration = self.tts_manager.getTTSDuration()
        if self.audio_duration > 0:
            self.increment = 100 / (self.audio_duration * 1000 / self.update_interval)  # Calculate increment per update
        else:
            self.increment = 0

    def update_progress_bar(self):
        if not self.is_paused and self.progress_value < 100:  # so the progress bar doesn't exceed 100%, also check if paused
            self.progress_value += self.increment
            self.progress_bar["value"] = self.progress_value
            self.timer_id = self.root.after(self.update_interval, self.update_progress_bar)  # Schedule next update

    def start_progress_bar(self):
        if self.timer_id:  # Cancel the previous timer if it exists
            self.root.after_cancel(self.timer_id)
        self.progress_value = 0  # Reset progress value
        self.progress_bar["value"] = 0  # Reset progress bar
        self.is_paused = False  # Set to False to start updating
        self.update_audio_duration()  # Update audio duration before starting
        self.update_progress_bar()  # Start updating the progress bar

    def reset_progress_bar(self):
        self.progress_bar.grid()  # Show the progress bar
        self.start_progress_bar()  # Restart the progress bar

    def hide_progress_bar(self):
        self.progress_bar.grid_remove()  # Hide the progress bar

    def pause_progress_bar(self):
        self.is_paused = True  # Pause progress bar

    def resume_progress_bar(self):
        self.is_paused = False  # Resume progress bar
        self.update_progress_bar()  # and continue updating


class TextManager:
    def __init__(self, root):
        self.root = root

        # Create the typing box
        self.typing_box = tk.Text(self.root, height=10, width=50, font=("Arial", 14))
        self.typing_box.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # Label to temporarily show results
        self.results_label = tk.Label(self.root, text="", font=("Arial", 24, "bold"), fg="blue")
        self.results_label.grid(row=0, column=1, pady=10, sticky="s")
        self.results_label.grid_remove()  # Hide the label initially

    def get_text(self):
        return self.typing_box.get("1.0", "end-1c")  # Get text from the typing box

    def clear_text(self):
        self.typing_box.delete("1.0", "end")  # Clear the typing box

    def show_results(self, results):
        self.results_label.config(text=results)  # Update the label text
        self.results_label.grid()  # Show the label

    def hide_results(self):
        self.results_label.grid_remove()  # Hide the label


class AudioTypingTest:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Typing Test")

        # to get screen size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}")

        # Set up the UI
        self.setup_ui()

        # Initialize managers
        self.tts_manager = ttsManager(self.root)

        # Generate TTS to get the duration initially
        self.tts_manager.TTSGenerate(self.tts_manager.getTypingText())

        self.progress_bar_manager = ProgressBarManager(self.root, self.tts_manager)
        self.text_manager = TextManager(self.root)

    def setup_ui(self):
        # grid layout
        self.root.columnconfigure(0, weight=1)  # Sidebar
        self.root.columnconfigure(1, weight=3)  # Main Typing Box
        self.root.columnconfigure(2, weight=1)  # Buttons
        self.root.rowconfigure(0, weight=1)  # Progress Bar
        self.root.rowconfigure(1, weight=4)  # Typing Area
        self.root.rowconfigure(2, weight=1)  # Bottom row

        # Title
        tk.Label(self.root, text="Audio Typing Test", font=("Times New Roman", 16, "bold")).grid(row=0, column=1, pady=10, sticky="n")

        # Sidebar
        self.sidebar = tk.Frame(self.root, bg="#ddd", width=500)
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsw")

        # Sidebar contents
        # Settings label
        self.settings_label = tk.Label(self.sidebar, text='Settings', font=("Times New Roman", 14))
        self.settings_label.grid(row=0, column=0, padx=10, pady=10, sticky="new")

        # Distortion
        # Label
        self.distortion_label = tk.Label(self.sidebar, text='Distortion:', font=("Times New Roman", 12))
        self.distortion_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        # Variable
        self.distortion_status = StringVar()
        
        # On
        self.distortion_on = tk.Radiobutton(self.sidebar, text="On", variable=self.distortion_status, value="on_distortion")
        self.distortion_on.grid(row=2, column=0, padx=10, pady=0, sticky="ew")
        
        # Off
        self.distortion_off = tk.Radiobutton(self.sidebar, text="Off", variable=self.distortion_status, value="off_distortion")
        self.distortion_off.grid(row=3, column=0, padx=10, pady=0, sticky="ew")

        # Set Default State
        self.distortion_status.set("off_distortion")

        # Show Text Box
        # Label
        self.show_text_box_label = tk.Label(self.sidebar, text="Show Text Box:", font=("Times New Roman", 12))
        self.show_text_box_label.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        
        # Variable
        self.text_box_status = StringVar()
        
        # On
        self.text_box_on = tk.Radiobutton(self.sidebar, text="Yes", variable=self.text_box_status, value="on_text_box")
        self.text_box_on.grid(row=5, column=0, padx=10, pady=0, sticky="ew")
        
        # Off
        self.text_box_on = tk.Radiobutton(self.sidebar, text="No", variable=self.text_box_status, value="off_text_box")
        self.text_box_on.grid(row=6, column=0, padx=10, pady=0, sticky="ew")

        # Set Default State
        self.text_box_status.set("on_text_box")
        
        # Additional Settings can go here if necessary
        

        # Sign in
        # Username
        # Label
        self.username_label = tk.Label(self.sidebar, text="Username:")
        self.username_label.grid(row=7, column=0, padx=10, pady=10, sticky="esw")
        
        # Variable
        self.username_value = StringVar()
        # Entry Box
        self.username_entry = ttk.Entry(self.sidebar, textvariable=self.username_value)
        self.username_entry.grid(row=8, column=0, padx=10, pady=0, sticky="esw")

        # Password
        # Label
        self.password_label = tk.Label(self.sidebar, text="Password:")
        self.password_label.grid(row=9, column=0, padx=10, pady=10, sticky="esw")
        
        # Variable
        self.password_value = StringVar()
        # Entry Box
        self.password_entry = ttk.Entry(self.sidebar, textvariable=self.password_value, show="*")
        self.password_entry.grid(row=10, column=0, padx=10, pady=0, sticky="esw")

        # Sign In Button
        self.sign_in_button = tk.Button(self.sidebar, text="Sign In", command=self.sign_in)
        self.sign_in_button.grid(row=11, column=0, padx=10, pady=0, sticky="esw")

        # Submit Button
        self.submit_button = tk.Button(self.root, text="Submit", command=self.submit_text)
        self.submit_button.grid(row=2, column=2, padx=10, pady=10, sticky="w")

        # Discard Button
        self.discard_button = tk.Button(self.root, text="Discard", command=self.discard_text)
        self.discard_button.grid(row=2, column=2, padx=10, pady=10, sticky="e")

        # Pause Button
        self.pause_button = tk.Button(self.root, text="\u23F8", font=("Arial", 14), command=self.pause_progress_bar)
        self.pause_button.grid(row=0, column=2, padx=10, pady=10, sticky="e")

        # Play Button
        self.play_button = tk.Button(self.root, text="\u25B6", font=("Arial", 14), command=self.resume_progress_bar)
        self.play_button.grid(row=0, column=2, padx=10, pady=10, sticky="w")

    # Placeholder function for sign in
    def sign_in(self):
        return "0"

    def submit_text(self):
        user_text = self.text_manager.get_text()  # Get text from the typing box

        # Calculate word count
        word_count = len(user_text.split())

        # Calculate words per minute
        minutes = self.tts_manager.getTTSDuration() / 60
        wpm = word_count / minutes if minutes > 0 else 0  # Prepare WPM to display

        # Calculate Accuracy
        reference_text = self.tts_manager.getTypingText()
        user_words = user_text.split()
        reference_words = reference_text.split()  # Audio Transcript
        correct_words = sum(1 for u, r in zip(user_words, reference_words) if u == r)
        accuracy = (correct_words / word_count) * 100
        results = f"You typed {word_count} words.\nWords per Minute: {wpm:.2f}\nAccuracy: {accuracy:.2f}"  # Accuracy will be added later

        # Hide the progress bar and show the results label
        self.progress_bar_manager.hide_progress_bar()
        self.text_manager.show_results(results)

        # Clear the typing box
        self.text_manager.clear_text()

        # After 5 seconds, hide the label and show the progress bar again
        self.root.after(5000, self.reset_ui)

    def reset_ui(self):
        self.text_manager.hide_results()  # Hide the results label
        self.progress_bar_manager.reset_progress_bar()  # Restart the progress bar

    def discard_text(self):
        self.text_manager.clear_text()  # Clear the typing box

    def pause_progress_bar(self):
        self.progress_bar_manager.pause_progress_bar()  # Pause the progress bar
        self.tts_manager.deleteTTSFile()

    def resume_progress_bar(self):
        self.tts_manager.TTSGenerate(self.tts_manager.getTypingText())
        self.tts_manager.playTTS()
        self.progress_bar_manager.reset_progress_bar()  # Restart the progress bar


# Create the main window
root = tk.Tk()

# Create an instance of the AudioTypingTest class
app = AudioTypingTest(root)

# Run the application
root.mainloop()
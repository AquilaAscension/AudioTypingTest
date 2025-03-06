from tkinter import *
import tkinter as tk
from tkinter import ttk

class ProgressBarManager:
    def __init__(self, root, audio_duration):
        self.root = root
        self.audio_duration = audio_duration
        self.update_interval = 100  # Update every 100 milliseconds
        self.increment = 100 / (self.audio_duration * 1000 / self.update_interval)  # Calculate increment per update
        self.progress_value = 0  # Track the progress bar value
        self.timer_id = None  # Track the timer ID
        self.is_paused = False

        # Create the progress bar
        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.grid(row=0, column=1, pady=10, sticky="s")
        self.progress_bar["maximum"] = 100  # Set a maximum value for the progress bar

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
        self.is_paused = False
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
        self.update_progress_bar() # and continue updating


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
        self.progress_bar_manager = ProgressBarManager(self.root, self.get_audio_duration())
        self.text_manager = TextManager(self.root)

        # Start the progress bar
        self.progress_bar_manager.start_progress_bar()

    def setup_ui(self):
        #grid layout
        self.root.columnconfigure(0, weight=1)  # Sidebar
        self.root.columnconfigure(1, weight=3)  # Main Typing Box
        self.root.columnconfigure(2, weight=1)  # Buttons
        self.root.rowconfigure(0, weight=1)  # Progress Bar
        self.root.rowconfigure(1, weight=4)  # Typing Area
        self.root.rowconfigure(2, weight=1)  # Bottom row

        # Title
        tk.Label(self.root, text="Audio Typing Test", font=("Times New Roman", 16, "bold")).grid(row=0, column=1, pady=10, sticky="n")

        # Sidebar
        self.sidebar = tk.Frame(self.root, bg="#ddd", width=150)
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="ns")

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

    def get_audio_duration(self):
        """
        This function will return the duration of the audio file.
        For now, it returns a default value of 60 seconds.
        """
        return 60  # Default duration in seconds

    def submit_text(self):
        user_text = self.text_manager.get_text()  # Get text from the typing box

        # Calculate word count
        word_count = len(user_text.split())
        results = f"You typed {word_count} words."  # Prepare results to display

        # Hide the progress bar and show the results label
        self.progress_bar_manager.hide_progress_bar()
        self.text_manager.show_results(results)

        # Clear the typing box
        self.text_manager.clear_text()

        # After 2 seconds, hide the label and show the progress bar again
        self.root.after(2000, self.reset_ui)

    def reset_ui(self):
        self.text_manager.hide_results()  # Hide the results label
        self.progress_bar_manager.reset_progress_bar()  # Restart the progress bar

    def discard_text(self):
        self.text_manager.clear_text()  # Clear the typing box

    def pause_progress_bar(self):
        self.progress_bar_manager.pause_progress_bar()  # Pause the progress bar

    def resume_progress_bar(self):
        self.progress_bar_manager.resume_progress_bar()  # Resume the progress bar


# Create the main window
root = tk.Tk()

# Create an instance of the AudioTypingTest class
app = AudioTypingTest(root)

# Run the application
root.mainloop()
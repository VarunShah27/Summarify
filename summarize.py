import tkinter as tk
from tkinter import ttk, scrolledtext 
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
import numpy as np
import ssl
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle SSL certificate for NLTK downloads
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

class TextSummarizer:
    def __init__(self):
        self.ensure_nltk_data()
        self.setup_gui()

    def ensure_nltk_data(self):
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            logger.info('Downloading required NLTK data...')
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            logger.info('NLTK data downloaded successfully')

    def preprocess_text(self, text):
        sentences = sent_tokenize(text)
        stop_words = set(stopwords.words('english'))
        
        clean_sentences = []
        for sentence in sentences:
            words = nltk.word_tokenize(sentence.lower())
            words = [word for word in words if word.isalnum() and word not in stop_words]
            clean_sentences.append(' '.join(words))
        
        return clean_sentences, sentences

    def sentence_similarity(self, sent1, sent2):
        words1 = sent1.split()
        words2 = sent2.split()
        
        if not words1 or not words2:
            return 0.0
        
        all_words = list(set(words1 + words2))
        vector1 = [0] * len(all_words)
        vector2 = [0] * len(all_words)
        
        for word in words1:
            vector1[all_words.index(word)] += 1
        for word in words2:
            vector2[all_words.index(word)] += 1
        
        if np.sum(vector1) == 0 or np.sum(vector2) == 0:
            return 0.0
        
        return 1 - cosine_distance(vector1, vector2)

    def build_similarity_matrix(self, sentences):
        similarity_matrix = np.zeros((len(sentences), len(sentences)))
        
        for i in range(len(sentences)):
            for j in range(len(sentences)):
                if i != j:
                    similarity_matrix[i][j] = self.sentence_similarity(sentences[i], sentences[j])
        
        return similarity_matrix

    def summarize_text(self, text, num_sentences=3):
        try:
            if not text or not isinstance(text, str):
                raise ValueError("Invalid input text")

            if len(text.strip()) == 0:
                raise ValueError("Empty text provided")

            clean_sentences, original_sentences = self.preprocess_text(text)
            
            if len(original_sentences) <= num_sentences:
                return text
            
            similarity_matrix = self.build_similarity_matrix(clean_sentences)
            sentence_scores = similarity_matrix.sum(axis=1)
            
            ranked_sentences = [(-score, index) for index, score in enumerate(sentence_scores)]
            ranked_sentences.sort()
            
            selected_indices = [ranked_sentences[i][1] for i in range(min(num_sentences, len(original_sentences)))]
            selected_indices.sort()
            
            summary = ' '.join([original_sentences[i] for i in selected_indices])
            return summary
        except Exception as e:
            logger.exception('Error in summarization')
            return f"Error: {str(e)}"

    def setup_gui(self):
        self.window = tk.Tk()
        self.window.title("Text Summarizer")
        self.window.geometry("800x600")

        # Configure style
        style = ttk.Style()
        style.configure('TButton', padding=6)
        style.configure('TLabel', padding=6)

        # Input frame
        input_frame = ttk.Frame(self.window, padding="10")
        input_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(input_frame, text="Enter your text:").pack(anchor=tk.W)
        
        self.input_text = scrolledtext.ScrolledText(input_frame, height=10, wrap=tk.WORD)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # Controls frame
        controls_frame = ttk.Frame(input_frame)
        controls_frame.pack(fill=tk.X, pady=5)

        ttk.Label(controls_frame, text="Number of sentences:").pack(side=tk.LEFT)
        self.sentence_count = ttk.Spinbox(controls_frame, from_=1, to=10, width=5)
        self.sentence_count.set(3)
        self.sentence_count.pack(side=tk.LEFT, padx=5)

        ttk.Button(controls_frame, text="Summarize", command=self.handle_summarize).pack(side=tk.RIGHT)

        # Output frame
        output_frame = ttk.Frame(self.window, padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(output_frame, text="Summary:").pack(anchor=tk.W)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=10, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=5)

    def handle_summarize(self):
        text = self.input_text.get("1.0", tk.END).strip()
        try:
            num_sentences = int(self.sentence_count.get())
        except ValueError:
            num_sentences = 3

        if not text:
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", "Please enter some text to summarize.")
            return

        summary = self.summarize_text(text, num_sentences)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", summary)

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = TextSummarizer()
    app.run()
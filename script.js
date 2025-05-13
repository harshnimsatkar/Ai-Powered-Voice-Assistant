// --- Get HTML Elements ---
const startButton = document.getElementById('startButton');
const userInputDisplay = document.getElementById('userInput');
const assistantOutputDisplay = document.getElementById('assistantOutput');
const statusMessage = document.getElementById('statusMessage');

// --- Backend API Endpoint ---
// IMPORTANT: This MUST match the address and port your Flask server (app.py) is running on.
const BACKEND_URL = 'http://127.0.0.1:5000/process';

// --- Check for Browser Support (Web Speech API) ---
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const SpeechSynthesis = window.speechSynthesis;

let recognition;
let isListening = false;

if (SpeechRecognition && SpeechSynthesis) {
    // --- Initialize Speech Recognition ---
    recognition = new SpeechRecognition();
    recognition.continuous = false; // Process after first pause in speech
    recognition.lang = 'en-US';    // Set language (adjust if needed)
    recognition.interimResults = false; // Get only final results
    recognition.maxAlternatives = 1; // Get the most likely result

    // --- Speech Recognition Event Handlers ---
    recognition.onstart = () => {
        isListening = true;
        statusMessage.textContent = 'Status: Listening...';
        startButton.textContent = '🛑 Stop Listening';
        startButton.classList.add('listening');
        startButton.disabled = false;
        userInputDisplay.textContent = '-'; // Clear previous input
        assistantOutputDisplay.textContent = '-'; // Clear previous output
        console.log('Speech recognition started');
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        userInputDisplay.textContent = transcript;
        statusMessage.textContent = 'Status: Processing...';
        startButton.disabled = true; // Disable button while backend processes
        console.log('Speech recognized:', transcript);

        // Send the transcript to the backend
        sendToBackend(transcript);
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        let errorMessage = `Error: ${event.error}`;
        if (event.error === 'no-speech') {
            errorMessage = "Error: No speech detected. Please try again.";
        } else if (event.error === 'audio-capture') {
            errorMessage = "Error: Microphone problem. Check connection & permissions.";
        } else if (event.error === 'not-allowed') {
            errorMessage = "Error: Microphone access denied. Please allow permission.";
        }
        statusMessage.textContent = errorMessage;
        stopListeningUI(); // Reset UI on error
    };

    recognition.onend = () => {
        // This event fires when recognition stops, either manually or automatically.
        // We only reset the UI fully if it wasn't stopped to start processing.
        if (isListening && !startButton.disabled) { // Only reset if not currently processing
             stopListeningUI();
        }
        console.log('Speech recognition ended');
    };

    // --- Button Click Handler ---
    startButton.addEventListener('click', () => {
        if (!isListening) {
            // Start listening
            try {
                recognition.start();
                // UI updates handled by recognition.onstart
            } catch (error) {
                 console.error("Error starting recognition:", error);
                 statusMessage.textContent = "Error: Could not start listening. Browser might require interaction first.";
                 startButton.disabled = false; // Keep enabled if start fails
            }
        } else {
            // Stop listening manually
            recognition.stop();
            stopListeningUI(); // Update UI immediately
        }
    });

} else {
    // --- Handle Lack of Browser Support ---
    statusMessage.textContent = "Status: Error - Your browser doesn't support the Web Speech API.";
    startButton.disabled = true;
    console.error("Web Speech API not supported in this browser.");
}

// --- Helper Function to Reset UI after stopping/error ---
function stopListeningUI() {
    isListening = false;
    statusMessage.textContent = 'Status: Idle';
    startButton.textContent = '🎤 Start Listening';
    startButton.classList.remove('listening');
    startButton.disabled = false; // Ensure button is usable again
}


// --- Function to Send Data to Backend ---
async function sendToBackend(text) {
    console.log('Sending to backend:', text);
    try {
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            // Send data as JSON in the format the backend expects
            body: JSON.stringify({ query: text }),
        });

        // Check if the request was successful
        if (!response.ok) {
            // Try to get error details from response body if available
            let errorBody = "No details provided.";
            try {
                const errorJson = await response.json();
                errorBody = errorJson.error || JSON.stringify(errorJson);
            } catch (parseError) {
                 // Ignore if response body isn't valid JSON
            }
            throw new Error(`Backend request failed! Status: ${response.status}. Details: ${errorBody}`);
        }

        const data = await response.json(); // Expecting { "reply": "..." } from Flask

        if (data && data.reply) {
            assistantOutputDisplay.textContent = data.reply;
            statusMessage.textContent = 'Status: Responded';
            console.log('Received reply from backend:', data.reply);
            speak(data.reply); // Speak the response from the backend
        } else {
            console.error("Invalid response format from backend:", data);
            throw new Error("Invalid response format received from backend.");
        }

    } catch (error) {
        console.error('Error communicating with backend:', error);
        assistantOutputDisplay.textContent = `Error: ${error.message}`;
        statusMessage.textContent = 'Status: Backend Error';
    } finally {
       // Re-enable the button after backend communication attempt is complete
       // (unless the assistant is about to speak, handled in speak())
       if (!SpeechSynthesis.speaking) {
            startButton.disabled = false;
       }
       // Ensure listening state is reset if backend call failed before recognition end event
       if (isListening) {
            stopListeningUI();
       }
    }
}

// --- Function to Speak Text using Browser's TTS ---
function speak(text) {
    if (!SpeechSynthesis) {
        console.warn("Speech Synthesis not supported.");
        startButton.disabled = false; // Enable button if we can't speak
        return;
    }
    // Cancel any previous speech first
    if (SpeechSynthesis.speaking) {
        console.log('Cancelling previous speech');
        SpeechSynthesis.cancel();
    }

    if (text && text.trim() !== '') {
        const utterance = new SpeechSynthesisUtterance(text);

        utterance.onstart = () => {
            console.log("SpeechSynthesis starting...");
            startButton.disabled = true; // Disable button while speaking
        };

        utterance.onerror = (event) => {
            console.error('SpeechSynthesis error:', event.error);
            // Append error info, don't overwrite the reply text
            assistantOutputDisplay.textContent += " (Error speaking response)";
            startButton.disabled = false; // Re-enable on error
            statusMessage.textContent = 'Status: Speech Error';
        };

        utterance.onend = () => {
            console.log("SpeechSynthesis finished.");
            startButton.disabled = false; // Re-enable button when done speaking
            // Reset status to Idle only after speaking finishes
            // statusMessage.textContent = 'Status: Idle'; // Or keep 'Responded'
        };

        // Optional: Select a voice
        // let voices = SpeechSynthesis.getVoices();
        // if (voices.length > 0) {
        //     utterance.voice = voices[0]; // Choose a specific voice
        // }

        SpeechSynthesis.speak(utterance);
    } else {
        console.log("No text provided to speak.");
        startButton.disabled = false; // Enable button if there's nothing to say
    }
}

// --- Initial Status Update ---
statusMessage.textContent = (SpeechRecognition && SpeechSynthesis) ? 'Status: Ready' : "Status: Error - Web Speech API Not Supported";
if (!SpeechRecognition || !SpeechSynthesis) {
    startButton.disabled = true;
}
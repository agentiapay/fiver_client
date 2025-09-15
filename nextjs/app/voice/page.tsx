"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import SpeechRecognition, { useSpeechRecognition } from "react-speech-recognition";
import { FaStethoscope, FaMicrophoneAlt } from "react-icons/fa";
import { v4 as uuidv4 } from "uuid";

export default function VoiceAgentPage() {
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>("");

  // 🎤 Speech recognition hook
  const { transcript, listening, resetTranscript, browserSupportsSpeechRecognition } =
    useSpeechRecognition();

  // ✅ Generate or restore conversationId
  useEffect(() => {
    const savedId = sessionStorage.getItem("conversationId");
    if (savedId) {
      setConversationId(savedId);
    } else {
      const newId = uuidv4();
      setConversationId(newId);
      sessionStorage.setItem("conversationId", newId);
    }
  }, []);

  // 📡 Send transcript to FastAPI backend
  const handleSend = async (text: string) => {
    if (!conversationId) return;

    setLoading(true);
    SpeechRecognition.stopListening();

    try {
      const res = await axios.post(
        "your backend url",
        { conversation_id: conversationId, voice: text },
        { responseType: "arraybuffer" } // ✅ receive audio
      );

      // 🎧 Convert bytes to audio and play
      const audioBlob = new Blob([res.data], { type: "audio/mpeg" });
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);

      audio.play();

      // Restart listening when audio ends
      audio.onended = () => {
        if (listening) {
          SpeechRecognition.startListening({ continuous: true, language: "en-IN" });
        }
      };
    } catch {
      alert("❌ Error connecting to server.");
      if (listening) {
        SpeechRecognition.startListening({ continuous: true, language: "en-IN" });
      }
    } finally {
      setLoading(false);
      resetTranscript();
    }
  };

  // ⏸️ Real-time improvement → 0.8s pause before sending
  useEffect(() => {
    if (transcript && !loading) {
      const timer = setTimeout(() => {
        handleSend(transcript);
      }, 800);
      return () => clearTimeout(timer);
    }
  }, [transcript]);

  // ▶️ Start conversation
  const startConversation = () => {
    if (!browserSupportsSpeechRecognition) {
      alert("Your browser does not support speech recognition.");
      return;
    }
    resetTranscript();
    SpeechRecognition.startListening({ continuous: true, language: "en-IN" });
  };

  // ⏹️ Stop conversation
  const stopConversation = () => {
    SpeechRecognition.stopListening();
  };

  // 🔄 Toggle function
  const toggleConversation = () => {
    if (listening) {
      stopConversation();
    } else {
      startConversation();
    }
  };

  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-50 to-blue-100">
      {/* Header */}
      <header className="absolute top-0 w-full flex justify-center items-center py-4 bg-white shadow-md">
        <FaStethoscope className="text-blue-600 text-2xl mr-2" />
        <h1 className="text-lg sm:text-xl font-bold text-gray-800">
          Doctor Voice Agent
        </h1>
      </header>

      {/* Center Section */}
      <main className="flex flex-col items-center justify-center flex-1 text-center px-4">
        <div className="bg-white shadow-lg rounded-2xl p-6 sm:p-8 max-w-md w-full">
          <div className="flex flex-col items-center">
            <FaMicrophoneAlt
              className={`text-6xl mb-4 transition ${
                listening ? "text-red-500 animate-pulse" : "text-blue-500"
              }`}
            />
            <h2 className="text-base sm:text-lg font-medium text-gray-700">
              {listening
                ? "Listening... please speak"
                : "Click the button to start conversation"}
            </h2>
            {loading && <p className="mt-3 text-gray-500 italic">Thinking...</p>}
          </div>

          {/* Toggle Button */}
          <button
            onClick={toggleConversation}
            className={`mt-6 w-full py-3 rounded-full font-semibold shadow-md transition ${
              listening
                ? "bg-red-500 text-white hover:bg-red-600"
                : "bg-green-500 text-white hover:bg-green-600"
            }`}
          >
            {listening ? "Stop Conversation" : "Start Conversation"}
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full text-center py-3 text-xs text-gray-500 bg-white shadow-inner">
        ⚕️ Your AI Doctor Assistant (with Audio Replies)
      </footer>
    </div>
  );
}

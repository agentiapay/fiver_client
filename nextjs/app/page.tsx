"use client";

import { useState, useRef, useEffect } from "react";
import { PiMicrophoneFill } from "react-icons/pi";
import { TfiArrowUp } from "react-icons/tfi";
import ReactMarkdown from "react-markdown";
import axios from "axios";
import SpeechRecognition, {
  useSpeechRecognition,
} from "react-speech-recognition";

type Message = {
  role: "user" | "assistant";
  text: string;
};

export default function Page() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const { transcript, listening, resetTranscript, browserSupportsSpeechRecognition } =
    useSpeechRecognition();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (listening) {
      setInput(transcript);
    }
  }, [transcript, listening]);

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    setMessages((prev) => [...prev, { role: "user", text: content }]);
    setInput("");
    resetTranscript();
    setLoading(true);

    try {
      const res = await axios.post("https://fiver-fastapi.vercel.app/chatbot", {
        prompt: content,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: res.data.response || "⚠️ No response from server",
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "❌ Error connecting to server." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !loading) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const handleVoiceToggle = () => {
    if (!browserSupportsSpeechRecognition) {
      alert("Your browser does not support voice recognition.");
      return;
    }
    if (listening) {
      SpeechRecognition.stopListening();
      if (transcript.trim()) {
        sendMessage(transcript);
      }
    } else {
      resetTranscript();
      SpeechRecognition.startListening({ continuous: true, language: "en-US" });
    }
  };

  return (
    <div className="h-[98vh] w-screen flex flex-col bg-[white]">
      {/* Logo Header */}
      <header className="absolute top-4 w-full flex justify-center z-10">
        <h1 className="text-lg font-semibold text-gray-800">🤖 AI Agent</h1>
      </header>

      {/* Chat Area */}
      <main className="flex-1 flex flex-col items-center justify-center px-2 sm:px-4 mt-10">
        <div className="w-full max-w-2xl flex-1 overflow-y-auto flex flex-col gap-4 py-6">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`px-4 py-3 rounded-2xl text-sm shadow-sm break-words prose prose-sm max-w-full
                  ${
                    m.role === "user"
                      ? "bg-gray-200 text-black "
                      : "bg-gray-100 text-black "
                  }`}
              >
                <ReactMarkdown>{m.text}</ReactMarkdown>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="px-4 py-3 rounded-2xl bg-gray-100 text-gray-500 text-sm animate-pulse">
                Typing...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input Box */}
        <div className="w-full max-w-3xl flex items-center gap-2 border rounded-full px-3 sm:px-4 py-2 shadow-sm mb-6 bg-white">
          <input
            type="text"
            className="flex-1 px-2 sm:px-3 py-2 rounded-full text-sm text-[black] outline-none"
            placeholder="Ask anything..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />

          {/* Voice Button */}
          <button
            onClick={handleVoiceToggle}
            className={`w-9 h-9 sm:w-10 sm:h-10 flex items-center justify-center rounded-full transition ${
              listening
                ? "bg-red-500 text-white hover:bg-red-600"
                : "bg-gray-300 text-gray-700 hover:bg-green-200 "
            }`}
          >
            <PiMicrophoneFill />
          </button>

          {/* Send Button */}
          <button
            onClick={() => sendMessage(input)}
            disabled={loading}
            className="w-9 h-9 sm:w-10 sm:h-10 flex items-center justify-center rounded-full bg-[#292626] text-white hover:bg-green-200 transition disabled:opacity-50"
          >
            <TfiArrowUp />
          </button>
        </div>
      </main>
    </div>
  );
}

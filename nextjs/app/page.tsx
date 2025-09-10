"use client";

import { useState, useRef, useEffect } from "react";
import { PiMicrophoneFill } from "react-icons/pi";
import { TfiArrowUp } from "react-icons/tfi";

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

  // speech recognition hook
  const { transcript, listening, resetTranscript, browserSupportsSpeechRecognition } =
    useSpeechRecognition();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // keep transcript in input while speaking
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
    <div className="h-screen w-screen flex flex-col bg-white">
      {/* Logo Header */}
      <header className="absolute top-4 w-full flex justify-center z-10">
        <h1 className="text-lg font-semibold text-gray-800">🤖 AI Agent</h1>
      </header>

      {/* Chat Area */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 mt-10">
        <div className="w-full max-w-2xl flex-1 overflow-y-auto flex flex-col gap-4 py-6">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`px-4 py-3 rounded-2xl max-w-[75%] text-sm shadow-sm
                  ${
                    m.role === "user"
                      ? "bg-gray-200 text-black"
                      : "bg-gray-100 text-gray-800 rounded-bl-none"
                  }`}
              >
                {m.text}
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
        <div className="w-full max-w-3xl flex items-center gap-2 border rounded-full px-4 py-2 shadow-sm mb-6 bg-white">
          <input
            type="text"
            className="flex-1 px-3 py-2 rounded-full text-sm outline-none"
            placeholder="Ask anything..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />

          {/* Voice Button */}
          <button
            onClick={handleVoiceToggle}
            className={`w-10 h-10 flex items-center justify-center rounded-full transition ${
              listening
                ? "bg-red-500 text-white hover:bg-red-600"
                : "bg-gray-300 text-gray-700 hover:bg-green-200 "
            }`}
          >
            {/* 🎤 */}
            {/* <MdOutlineMic /> */}
            <PiMicrophoneFill />

          </button>

          {/* Send Button */}
          <button
            onClick={() => sendMessage(input)}
            disabled={loading}
            className="w-10 h-10 flex items-center justify-center rounded-full bg-[#292626]  text-white hover:bg-green-200 transition disabled:opacity-50"
          >
            <TfiArrowUp />
            





          </button>
        </div>
      </main>
    </div>
  );
}

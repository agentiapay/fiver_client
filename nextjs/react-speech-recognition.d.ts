declare module "react-speech-recognition" {
  export interface ListeningOptions {
    continuous?: boolean;
    language?: string;
  }

  export function startListening(options?: ListeningOptions): void;
  export function stopListening(): void;

  export interface SpeechRecognitionHook {
    transcript: string;
    listening: boolean;
    resetTranscript: () => void;
    browserSupportsSpeechRecognition: boolean;
  }

  export function useSpeechRecognition(): SpeechRecognitionHook;

  const SpeechRecognition: {
    startListening: typeof startListening;
    stopListening: typeof stopListening;
  };

  export default SpeechRecognition;
}

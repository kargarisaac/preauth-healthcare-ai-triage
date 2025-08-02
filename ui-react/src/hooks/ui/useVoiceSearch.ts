import { useState, useEffect, useCallback, useRef } from 'react';
import { VoiceSearchCapability } from '../../types/healthcare';

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  serviceURI: string;
  grammars: SpeechGrammarList;
  start(): void;
  stop(): void;
  abort(): void;
  addEventListener(type: 'result', listener: (event: SpeechRecognitionEvent) => void): void;
  addEventListener(type: 'error', listener: (event: SpeechRecognitionErrorEvent) => void): void;
  addEventListener(type: 'start' | 'end' | 'speechstart' | 'speechend' | 'soundstart' | 'soundend' | 'audiostart' | 'audioend' | 'nomatch', listener: (event: Event) => void): void;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

interface VoiceSearchOptions {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  maxAlternatives?: number;
  timeout?: number;
  autoStop?: boolean;
}

const DEFAULT_OPTIONS: Required<VoiceSearchOptions> = {
  language: 'en-US',
  continuous: false,
  interimResults: true,
  maxAlternatives: 3,
  timeout: 10000, // 10 seconds
  autoStop: true
};

export const useVoiceSearch = (options: VoiceSearchOptions = {}) => {
  const config = { ...DEFAULT_OPTIONS, ...options };
  
  const [voiceCapability, setVoiceCapability] = useState<VoiceSearchCapability>({
    isSupported: false,
    isListening: false,
    confidence: 0,
    transcript: '',
    error: undefined
  });

  const [interimTranscript, setInterimTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isManualStop = useRef(false);

  // Check for speech recognition support
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const isSupported = !!SpeechRecognition;
    
    setVoiceCapability(prev => ({
      ...prev,
      isSupported
    }));

    if (isSupported && !recognitionRef.current) {
      recognitionRef.current = new SpeechRecognition();
      setupRecognition();
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Setup speech recognition configuration and event handlers
  const setupRecognition = useCallback(() => {
    if (!recognitionRef.current) return;

    const recognition = recognitionRef.current;
    
    // Configure recognition
    recognition.continuous = config.continuous;
    recognition.interimResults = config.interimResults;
    recognition.lang = config.language;
    recognition.maxAlternatives = config.maxAlternatives;

    // Handle recognition results
    recognition.addEventListener('result', (event: SpeechRecognitionEvent) => {
      let interim = '';
      let final = '';
      let maxConfidence = 0;

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const transcript = result[0].transcript;
        const confidence = result[0].confidence || 0;
        
        maxConfidence = Math.max(maxConfidence, confidence);
        
        if (result.isFinal) {
          final += transcript;
        } else {
          interim += transcript;
        }
      }

      setInterimTranscript(interim);
      if (final) {
        setFinalTranscript(prev => prev + final);
        setVoiceCapability(prev => ({
          ...prev,
          transcript: prev.transcript + final,
          confidence: maxConfidence
        }));
      }
    });

    // Handle recognition start
    recognition.addEventListener('start', () => {
      setVoiceCapability(prev => ({
        ...prev,
        isListening: true,
        error: undefined
      }));
      
      // Set timeout for auto-stop
      if (config.autoStop && config.timeout > 0) {
        timeoutRef.current = setTimeout(() => {
          stopListening();
        }, config.timeout);
      }
    });

    // Handle recognition end
    recognition.addEventListener('end', () => {
      setVoiceCapability(prev => ({
        ...prev,
        isListening: false
      }));
      
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
      
      setInterimTranscript('');
    });

    // Handle recognition errors
    recognition.addEventListener('error', (event: SpeechRecognitionErrorEvent) => {
      let errorMessage = 'Voice recognition error occurred';
      
      switch (event.error) {
        case 'no-speech':
          errorMessage = 'No speech detected. Please try again.';
          break;
        case 'audio-capture':
          errorMessage = 'Microphone access denied or unavailable.';
          break;
        case 'not-allowed':
          errorMessage = 'Microphone access denied. Please allow microphone access.';
          break;
        case 'network':
          errorMessage = 'Network error during voice recognition.';
          break;
        case 'service-not-allowed':
          errorMessage = 'Voice recognition service not available.';
          break;
        case 'bad-grammar':
          errorMessage = 'Speech recognition grammar error.';
          break;
        case 'language-not-supported':
          errorMessage = `Language "${config.language}" not supported.`;
          break;
        default:
          errorMessage = `Voice recognition error: ${event.error}`;
      }
      
      setVoiceCapability(prev => ({
        ...prev,
        isListening: false,
        error: errorMessage
      }));
    });

    // Handle speech start/end events
    recognition.addEventListener('speechstart', () => {
      setVoiceCapability(prev => ({
        ...prev,
        error: undefined
      }));
    });

    recognition.addEventListener('speechend', () => {
      if (config.autoStop && !config.continuous) {
        stopListening();
      }
    });

  }, [config]);

  // Start voice recognition
  const startListening = useCallback(() => {
    if (!voiceCapability.isSupported || !recognitionRef.current) {
      setVoiceCapability(prev => ({
        ...prev,
        error: 'Voice recognition not supported'
      }));
      return;
    }

    if (voiceCapability.isListening) {
      return; // Already listening
    }

    try {
      // Reset transcripts
      setInterimTranscript('');
      setFinalTranscript('');
      setVoiceCapability(prev => ({
        ...prev,
        transcript: '',
        confidence: 0,
        error: undefined
      }));
      
      isManualStop.current = false;
      recognitionRef.current.start();
    } catch (error) {
      setVoiceCapability(prev => ({
        ...prev,
        error: 'Failed to start voice recognition'
      }));
    }
  }, [voiceCapability.isSupported, voiceCapability.isListening]);

  // Stop voice recognition
  const stopListening = useCallback(() => {
    if (!recognitionRef.current || !voiceCapability.isListening) {
      return;
    }

    try {
      isManualStop.current = true;
      recognitionRef.current.stop();
    } catch (error) {
      setVoiceCapability(prev => ({
        ...prev,
        error: 'Failed to stop voice recognition'
      }));
    }
  }, [voiceCapability.isListening]);

  // Toggle listening state
  const toggleListening = useCallback(() => {
    if (voiceCapability.isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [voiceCapability.isListening, startListening, stopListening]);

  // Clear transcript
  const clearTranscript = useCallback(() => {
    setInterimTranscript('');
    setFinalTranscript('');
    setVoiceCapability(prev => ({
      ...prev,
      transcript: '',
      confidence: 0,
      error: undefined
    }));
  }, []);

  // Reset voice search state
  const resetVoiceSearch = useCallback(() => {
    if (voiceCapability.isListening) {
      stopListening();
    }
    clearTranscript();
  }, [voiceCapability.isListening, stopListening, clearTranscript]);

  // Get current full transcript (final + interim)
  const getCurrentTranscript = useCallback(() => {
    return finalTranscript + interimTranscript;
  }, [finalTranscript, interimTranscript]);

  // Voice search specific commands for healthcare
  const processHealthcareVoiceCommand = useCallback((transcript: string) => {
    const cleanTranscript = transcript.toLowerCase().trim();
    
    // Common healthcare voice commands
    const commands = {
      // Search patterns
      searchMember: /(?:search|find|look for|show me)\s+(?:member|patient)\s+(.+)/,
      searchById: /(?:search|find|look for)\s+(?:id|emirates id|member id)\s+(.+)/,
      searchByPhone: /(?:search|find|look for)\s+phone\s+(.+)/,
      searchByPolicy: /(?:search|find|look for)\s+policy\s+(?:number)?\s*(.+)/,
      
      // Navigation patterns
      showProfile: /(?:show|open|display)\s+(?:profile|details)\s+(?:for|of)\s+(.+)/,
      showHistory: /(?:show|open|display)\s+(?:history|timeline)\s+(?:for|of)\s+(.+)/,
      showGaps: /(?:show|open|display)\s+(?:care gaps|gaps|alerts)\s+(?:for|of)\s+(.+)/,
      
      // Actions
      approve: /(?:approve|accept)\s+(.+)/,
      deny: /(?:deny|reject|decline)\s+(.+)/,
      schedule: /(?:schedule|book)\s+(.+)/
    };
    
    for (const [action, pattern] of Object.entries(commands)) {
      const match = cleanTranscript.match(pattern);
      if (match) {
        return {
          action,
          value: match[1]?.trim(),
          originalTranscript: transcript,
          confidence: voiceCapability.confidence
        };
      }
    }
    
    // Return raw search if no specific command matched
    return {
      action: 'search',
      value: transcript.trim(),
      originalTranscript: transcript,
      confidence: voiceCapability.confidence
    };
  }, [voiceCapability.confidence]);

  // Process final transcript for healthcare commands
  const processVoiceCommand = useCallback(() => {
    if (!finalTranscript) return null;
    
    return processHealthcareVoiceCommand(finalTranscript);
  }, [finalTranscript, processHealthcareVoiceCommand]);

  return {
    // State
    ...voiceCapability,
    interimTranscript,
    finalTranscript,
    
    // Actions
    startListening,
    stopListening,
    toggleListening,
    clearTranscript,
    resetVoiceSearch,
    
    // Utilities
    getCurrentTranscript,
    processVoiceCommand,
    processHealthcareVoiceCommand,
    
    // Configuration
    isConfigured: !!recognitionRef.current,
    language: config.language,
    continuous: config.continuous
  };
};

export default useVoiceSearch;
import { useState, useEffect, useCallback, useRef } from 'react';
import { BarcodeSearchResult } from '../../types/healthcare';

interface BarcodeScannerConfig {
  video?: {
    width?: number;
    height?: number;
    facingMode?: 'user' | 'environment';
  };
  audio?: boolean;
  formats?: string[];
  continuous?: boolean;
  timeout?: number;
}

interface ScannerState {
  isScanning: boolean;
  isInitialized: boolean;
  error: string | null;
  hasPermission: boolean | null;
  stream: MediaStream | null;
  lastResult: BarcodeSearchResult | null;
}

const DEFAULT_CONFIG: Required<BarcodeScannerConfig> = {
  video: {
    width: 640,
    height: 480,
    facingMode: 'environment'
  },
  audio: false,
  formats: ['code_128', 'code_39', 'ean_13', 'ean_8', 'qr_code', 'data_matrix'],
  continuous: false,
  timeout: 30000
};

// Mock barcode detection - in a real implementation, you would use a library like QuaggaJS or ZXing
const mockBarcodeDetection = (imageData: ImageData): Promise<BarcodeSearchResult | null> => {
  return new Promise((resolve) => {
    // Simulate processing time
    setTimeout(() => {
      // Mock detection logic - in reality this would analyze the image data
      const mockResults: BarcodeSearchResult[] = [
        {
          type: 'emirates_id',
          value: '784-1234-5678901-0',
          confidence: 0.95
        },
        {
          type: 'insurance_card',
          value: 'DHI-789456123',
          confidence: 0.88
        },
        {
          type: 'member_id',
          value: 'MBR-001234567',
          confidence: 0.92
        }
      ];
      
      // Simulate random detection success (70% chance)
      if (Math.random() > 0.3) {
        const randomResult = mockResults[Math.floor(Math.random() * mockResults.length)];
        resolve(randomResult);
      } else {
        resolve(null);
      }
    }, 100);
  });
};

export const useBarcodeScanner = (config: BarcodeScannerConfig = {}) => {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };
  
  const [state, setState] = useState<ScannerState>({
    isScanning: false,
    isInitialized: false,
    error: null,
    hasPermission: null,
    stream: null,
    lastResult: null
  });

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Check if barcode scanning is supported
  const isSupported = useCallback(() => {
    return !!(
      navigator.mediaDevices &&
      navigator.mediaDevices.getUserMedia &&
      window.HTMLCanvasElement &&
      HTMLCanvasElement.prototype.getContext
    );
  }, []);

  // Request camera permission
  const requestPermission = useCallback(async (): Promise<boolean> => {
    if (!isSupported()) {
      setState(prev => ({ ...prev, error: 'Barcode scanning not supported on this device' }));
      return false;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: finalConfig.video,
        audio: finalConfig.audio
      });
      
      setState(prev => ({ 
        ...prev, 
        hasPermission: true, 
        stream,
        error: null 
      }));
      
      return true;
    } catch (error) {
      let errorMessage = 'Camera access denied';
      
      if (error instanceof Error) {
        switch (error.name) {
          case 'NotAllowedError':
            errorMessage = 'Camera access denied. Please allow camera permissions.';
            break;
          case 'NotFoundError':
            errorMessage = 'No camera found on this device.';
            break;
          case 'NotReadableError':
            errorMessage = 'Camera is being used by another application.';
            break;
          case 'OverconstrainedError':
            errorMessage = 'Camera constraints could not be satisfied.';
            break;
          default:
            errorMessage = `Camera error: ${error.message}`;
        }
      }
      
      setState(prev => ({ 
        ...prev, 
        hasPermission: false, 
        error: errorMessage 
      }));
      
      return false;
    }
  }, [finalConfig, isSupported]);

  // Initialize video stream
  const initializeVideo = useCallback(async (videoElement: HTMLVideoElement) => {
    if (!state.stream) {
      const hasPermission = await requestPermission();
      if (!hasPermission) return false;
    }

    try {
      videoElement.srcObject = state.stream;
      videoElement.setAttribute('playsinline', 'true');
      videoElement.setAttribute('muted', 'true');
      
      return new Promise<boolean>((resolve) => {
        videoElement.onloadedmetadata = () => {
          videoElement.play()
            .then(() => {
              setState(prev => ({ ...prev, isInitialized: true, error: null }));
              resolve(true);
            })
            .catch((error) => {
              setState(prev => ({ ...prev, error: `Failed to start video: ${error.message}` }));
              resolve(false);
            });
        };
        
        videoElement.onerror = () => {
          setState(prev => ({ ...prev, error: 'Failed to load video stream' }));
          resolve(false);
        };
      });
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Failed to initialize video' 
      }));
      return false;
    }
  }, [state.stream, requestPermission]);

  // Capture frame and analyze for barcodes
  const analyzeFrame = useCallback(async (): Promise<BarcodeSearchResult | null> => {
    if (!videoRef.current || !canvasRef.current) return null;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    if (!ctx) return null;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw current frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Get image data for analysis
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    
    // Analyze for barcodes (using mock detection)
    return await mockBarcodeDetection(imageData);
  }, []);

  // Scanning loop
  const scanningLoop = useCallback(async () => {
    if (!state.isScanning) return;

    try {
      const result = await analyzeFrame();
      
      if (result && result.confidence > 0.7) {
        setState(prev => ({ ...prev, lastResult: result }));
        
        if (!finalConfig.continuous) {
          stopScanning();
        }
        
        return;
      }
    } catch (error) {
      console.error('Barcode analysis error:', error);
    }

    // Continue scanning
    if (state.isScanning) {
      animationFrameRef.current = requestAnimationFrame(scanningLoop);
    }
  }, [state.isScanning, analyzeFrame, finalConfig.continuous]);

  // Start scanning
  const startScanning = useCallback(async (
    videoElement?: HTMLVideoElement,
    canvasElement?: HTMLCanvasElement
  ) => {
    if (state.isScanning) return false;

    // Set refs if provided
    if (videoElement) videoRef.current = videoElement;
    if (canvasElement) canvasRef.current = canvasElement;

    if (!videoRef.current) {
      setState(prev => ({ ...prev, error: 'Video element not provided' }));
      return false;
    }

    setState(prev => ({ ...prev, isScanning: true, error: null, lastResult: null }));

    // Initialize video if needed
    if (!state.isInitialized) {
      const initialized = await initializeVideo(videoRef.current);
      if (!initialized) {
        setState(prev => ({ ...prev, isScanning: false }));
        return false;
      }
    }

    // Set timeout if configured
    if (finalConfig.timeout > 0) {
      timeoutRef.current = setTimeout(() => {
        stopScanning();
        setState(prev => ({ ...prev, error: 'Scanning timeout reached' }));
      }, finalConfig.timeout);
    }

    // Start scanning loop
    scanningLoop();
    
    return true;
  }, [state.isScanning, state.isInitialized, initializeVideo, scanningLoop, finalConfig.timeout]);

  // Stop scanning
  const stopScanning = useCallback(() => {
    setState(prev => ({ ...prev, isScanning: false }));
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  // Reset scanner state
  const reset = useCallback(() => {
    stopScanning();
    setState(prev => ({ 
      ...prev, 
      lastResult: null, 
      error: null,
      isInitialized: false
    }));
    
    if (state.stream) {
      state.stream.getTracks().forEach(track => track.stop());
      setState(prev => ({ ...prev, stream: null, hasPermission: null }));
    }
  }, [stopScanning, state.stream]);

  // Toggle camera facing mode (front/back)
  const toggleCamera = useCallback(async () => {
    const newFacingMode = finalConfig.video.facingMode === 'environment' ? 'user' : 'environment';
    
    // Stop current stream
    if (state.stream) {
      state.stream.getTracks().forEach(track => track.stop());
    }
    
    // Request new stream with different facing mode
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { ...finalConfig.video, facingMode: newFacingMode },
        audio: finalConfig.audio
      });
      
      setState(prev => ({ ...prev, stream, isInitialized: false }));
      
      // Reinitialize if we have a video element
      if (videoRef.current) {
        await initializeVideo(videoRef.current);
      }
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Failed to switch camera' 
      }));
    }
  }, [finalConfig, state.stream, initializeVideo]);

  // Parse barcode result to extract healthcare information
  const parseHealthcareBarcode = useCallback((result: BarcodeSearchResult) => {
    const { type, value } = result;
    
    switch (type) {
      case 'emirates_id':
        // Emirates ID format: 784-YYYY-NNNNNNN-D
        const emiratesIdMatch = value.match(/^784-\d{4}-\d{7}-\d$/);
        return {
          isValid: !!emiratesIdMatch,
          searchType: 'emiratesId',
          searchValue: value,
          displayName: 'Emirates ID'
        };
        
      case 'insurance_card':
        // Insurance card format varies by provider
        return {
          isValid: value.length >= 6,
          searchType: 'policyNumber',
          searchValue: value,
          displayName: 'Policy Number'
        };
        
      case 'member_id':
        // Member ID format
        return {
          isValid: value.length >= 6,
          searchType: 'memberId',
          searchValue: value,
          displayName: 'Member ID'
        };
        
      default:
        return {
          isValid: false,
          searchType: 'query',
          searchValue: value,
          displayName: 'Unknown Format'
        };
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      reset();
    };
  }, [reset]);

  return {
    // State
    isScanning: state.isScanning,
    isInitialized: state.isInitialized,
    hasPermission: state.hasPermission,
    error: state.error,
    lastResult: state.lastResult,
    
    // Actions
    startScanning,
    stopScanning,
    reset,
    toggleCamera,
    requestPermission,
    
    // Utilities
    isSupported,
    parseHealthcareBarcode,
    
    // Refs for video and canvas elements
    setVideoRef: (ref: HTMLVideoElement | null) => { videoRef.current = ref; },
    setCanvasRef: (ref: HTMLCanvasElement | null) => { canvasRef.current = ref; }
  };
};

export default useBarcodeScanner;
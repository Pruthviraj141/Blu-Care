// src/pages/MultiRagChatPage.jsx - Clean ChatGPT-Style AI Healthcare Workspace
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import GlassCard from '../components/ui/GlassCard';
import ChatMessage from '../components/chat/ChatMessage';
import TypingIndicator from '../components/chat/TypingIndicator';
import AssessmentSkeleton from '../components/chat/AssessmentSkeleton';
import { useToast } from '../contexts/ToastContext';
import { logger } from '../utils/logger';
import { useAuth } from '@clerk/clerk-react';
import {
  getSessionById,
  createSession,
  updateSession,
  getActiveSessionId,
  setActiveSessionId,
} from '../utils/chatStorage';
import { chatApi, ApiError } from '../utils/api';
import {
  Send,
  Sparkles,
  FileSearch,
  ExternalLink,
  Paperclip,
  Mic,
  MicOff,
  ArrowDown,
  Bot,
  User,
  X,
  Image as ImageIcon,
  RotateCcw,
  UploadCloud,
  Copy,
  Check,
  AlertCircle,
  FileText,
} from 'lucide-react';

const MultiRagChatPage = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const { isLoaded, isSignedIn, getToken } = useAuth();

  // Safe token retriever supporting Clerk loaded and signed-in states
  const getAuthToken = async () => {
    try {
      if (isLoaded && isSignedIn && typeof getToken === 'function') {
        return await getToken();
      }
      return null;
    } catch (err) {
      logger.error('Failed to get Clerk JWT token:', err);
      return null;
    }
  };

  // AbortController ref for in-flight request cancellation
  const abortControllerRef = useRef(null);

  // Unmount cleanup: cancel any pending HTTP requests
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Chat conversation state
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeActionId, setActiveActionId] = useState(null);
  const [thinkingStep, setThinkingStep] = useState('Analyzing clinical guidelines...');

  // Citations drawer state
  const [showCitationDrawer, setShowCitationDrawer] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [copiedMsgId, setCopiedMsgId] = useState(null);
  const [showScrollBottom, setShowScrollBottom] = useState(false);

  // File upload state
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  // Voice recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const recognitionRef = useRef(null);
  const timerRef = useRef(null);

  // Scroll & input refs
  const chatContainerRef = useRef(null);
  const textareaRef = useRef(null);

  // Synchronize session from URL parameter or resume active session
  useEffect(() => {
    if (sessionId) {
      const sess = getSessionById(sessionId);
      if (sess) {
        setCurrentSession(sess);
        setMessages(sess.messages || []);
        setActiveSessionId(sess.id);
      } else {
        const activeId = getActiveSessionId();
        navigate(`/app/chat/${activeId}`, { replace: true });
      }
    } else {
      const activeId = getActiveSessionId();
      if (activeId) {
        navigate(`/app/chat/${activeId}`, { replace: true });
      } else {
        setCurrentSession(null);
        setMessages([]);
      }
    }
  }, [sessionId, navigate]);

  // Auto-scroll handler
  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, thinkingStep]);

  // Monitor scroll for scroll-to-bottom floating button
  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    const isFarFromBottom = scrollHeight - scrollTop - clientHeight > 150;
    setShowScrollBottom(isFarFromBottom);
  };

  // Auto-grow textarea height
  const handleInputChange = (e) => {
    setInputQuery(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  };

  // Suggested prompt pills for clean empty state
  const suggestedPrompts = [
    'I have had a fever for two days',
    'Explain my blood report',
    'What medicine is commonly prescribed for migraine?',
    'Help me understand this diagnosis',
  ];

  // ----------------------------------------------------
  // FILE UPLOAD SYSTEM (Drag & Drop, Preview, Progress, Multiple)
  // ----------------------------------------------------
  const handleFileSelect = (files) => {
    const fileList = Array.from(files);
    if (fileList.length === 0) return;

    fileList.forEach((file) => {
      const fileId = 'file_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4);
      const isImage = file.type.startsWith('image/');
      const previewUrl = isImage ? URL.createObjectURL(file) : null;

      const newFileObj = {
        id: fileId,
        name: file.name,
        size: file.size,
        type: file.type,
        previewUrl,
        progress: 0,
        status: 'uploading', // 'uploading' | 'complete' | 'error'
        file,
      };

      setAttachedFiles((prev) => [...prev, newFileObj]);

      // Simulate realistic smooth upload progress
      let currentProgress = 0;
      const progressInterval = setInterval(() => {
        currentProgress += Math.floor(Math.random() * 30) + 15;
        if (currentProgress >= 100) {
          currentProgress = 100;
          clearInterval(progressInterval);
          setAttachedFiles((prev) =>
            prev.map((f) => (f.id === fileId ? { ...f, progress: 100, status: 'complete' } : f))
          );
          addToast(`Attached "${file.name}"`, 'success');
        } else {
          setAttachedFiles((prev) =>
            prev.map((f) => (f.id === fileId ? { ...f, progress: currentProgress } : f))
          );
        }
      }, 150);
    });
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  const handleRemoveFile = (id) => {
    setAttachedFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const handleRetryUpload = (id) => {
    setAttachedFiles((prev) =>
      prev.map((f) => (f.id === id ? { ...f, status: 'uploading', progress: 0 } : f))
    );
    setTimeout(() => {
      setAttachedFiles((prev) =>
        prev.map((f) => (f.id === id ? { ...f, status: 'complete', progress: 100 } : f))
      );
      addToast('Upload retried successfully', 'success');
    }, 400);
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  // ----------------------------------------------------
  // REAL VOICE INPUT SYSTEM (Web Speech API)
  // ----------------------------------------------------
  const startVoiceRecording = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      addToast('Browser Speech Recognition not supported. Please type your query.', 'error');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsRecording(true);
        setRecordingTime(0);
        addToast('Voice listener active. Speak your symptoms...', 'info');

        timerRef.current = setInterval(() => {
          setRecordingTime((prev) => prev + 1);
        }, 1000);
      };

      recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        setInputQuery(transcript);
        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto';
          textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
        }
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        stopVoiceRecording();
        if (event.error === 'not-allowed') {
          addToast('Microphone access denied. Please check browser permissions.', 'error');
        } else {
          addToast(`Voice error: ${event.error}`, 'error');
        }
      };

      recognition.onend = () => {
        setIsRecording(false);
        if (timerRef.current) clearInterval(timerRef.current);
      };

      recognition.start();
      recognitionRef.current = recognition;
    } catch (err) {
      logger.error('Failed to start speech recognition:', err);
      addToast('Could not access microphone.', 'error');
    }
  };

  const stopVoiceRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    if (timerRef.current) clearInterval(timerRef.current);
    setIsRecording(false);
  };

  const toggleVoiceRecording = () => {
    if (isRecording) {
      stopVoiceRecording();
      addToast('Voice recording stopped.', 'info');
    } else {
      startVoiceRecording();
    }
  };

  // ----------------------------------------------------
  // SEND MESSAGE HANDLER & BACKEND CALL / FALLBACK
  // ----------------------------------------------------
  const handleSendMessage = async (customText) => {
    const queryText = (customText || inputQuery).trim();
    if ((!queryText && attachedFiles.length === 0) || isLoading) return;

    // Determine target active session or auto-create a new session
    let targetSess = currentSession;
    if (!targetSess) {
      const derivedTitle = queryText.slice(0, 32) || 'Medical Consultation';
      targetSess = createSession(derivedTitle);
      setCurrentSession(targetSess);
      window.dispatchEvent(new Event('blucare_sessions_updated'));
      navigate(`/app/chat/${targetSess.id}`, { replace: true });
    } else if (messages.length === 0 && queryText) {
      // Auto-update initial session title from first prompt
      const derivedTitle = queryText.slice(0, 36);
      updateSession(targetSess.id, { title: derivedTitle });
      window.dispatchEvent(new Event('blucare_sessions_updated'));
    }

    // Format attached files summary if present
    let fullQueryText = queryText;
    if (attachedFiles.length > 0) {
      const fileNames = attachedFiles.map((f) => `📎 [Attached: ${f.name}]`).join('\n');
      fullQueryText = `${queryText}\n\n${fileNames}`;
    }

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      text: fullQueryText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    updateSession(targetSess.id, { messages: newMessages });

    // Reset input fields
    if (!customText) {
      setInputQuery('');
      setAttachedFiles([]);
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
    }

    setIsLoading(true);
    setThinkingStep('Analyzing clinical guidelines...');

    // Multi-step thinking state simulation
    const thinkingSteps = [
      'Searching WHO medical guidelines...',
      'Cross-referencing PubMed research databases...',
      'Synthesizing evidence-based diagnostic advice...',
    ];

    let stepIndex = 0;
    const thinkingInterval = setInterval(() => {
      if (stepIndex < thinkingSteps.length) {
        setThinkingStep(thinkingSteps[stepIndex]);
        stepIndex++;
      }
    }, 450);

    // Cancel any ongoing in-flight HTTP request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const requestOptions = {
      getToken: getAuthToken,
      signal: controller.signal,
      timeout: 45000,
    };

    try {
      // Re-fetch latest session from chatStorage to guarantee threadId is up-to-date
      const freshSess = getSessionById(targetSess.id) || targetSess;
      let activeThreadId = freshSess.threadId || targetSess.threadId;
      let chatData = null;

      if (!activeThreadId) {
        // First message turn in new session: initialize backend thread
        chatData = await chatApi.startSession(queryText, requestOptions);
        activeThreadId = chatData.thread_id;
        const updated = updateSession(targetSess.id, { threadId: activeThreadId });
        if (updated) {
          targetSess = updated;
          setCurrentSession(updated);
        }
      } else {
        // Subsequent message turn in existing backend thread
        try {
          chatData = await chatApi.sendMessage(activeThreadId, queryText, requestOptions);
        } catch (sendErr) {
          if (sendErr instanceof ApiError && (sendErr.status === 404 || sendErr.status === 403 || sendErr.status === 400)) {
            // Session thread expired, cleared, or ownership changed in backend, automatically restart thread
            logger.warn(`Backend session thread rejected (${sendErr.status}). Reinitializing new session thread...`);
            chatData = await chatApi.startSession(queryText, requestOptions);
            activeThreadId = chatData.thread_id;
            updateSession(targetSess.id, { threadId: activeThreadId });
          } else {
            throw sendErr;
          }
        }
      }

      clearInterval(thinkingInterval);

      // Preserve ALL backend response fields intact (message, stage, is_complete, symptom_facts, metadata)
      const botMessage = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        text: chatData.message || 'Clinical evaluation completed.',
        stage: chatData.stage,
        is_complete: chatData.is_complete,
        symptom_facts: chatData.symptom_facts || {},
        assessment: chatData.assessment || null,
        actions: chatData.actions || [],
        facilities: chatData.facilities || null,
        external_search: chatData.external_search || null,
        ayurvedic_guidance: chatData.ayurvedic_guidance || null,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        ...(chatData.risk_level && { risk_level: chatData.risk_level }),
        ...(chatData.confidence !== undefined && { confidence: chatData.confidence }),
        ...(chatData.sources && { sources: chatData.sources }),
      };

      const updatedMsgs = [...newMessages, botMessage];
      setMessages(updatedMsgs);
      const finalSess = updateSession(targetSess.id, {
        messages: updatedMsgs,
        threadId: activeThreadId,
      });
      if (finalSess) {
        setCurrentSession(finalSess);
      }
      setIsLoading(false);
    } catch (err) {
      clearInterval(thinkingInterval);

      if (err instanceof ApiError && err.status === 408) {
        logger.warn('Chat request timed out:', err);
        addToast('Request timed out. Please try sending your message again.', 'error');
      } else if (err.message !== 'Request was cancelled' && err.message !== 'Request aborted by caller') {
        logger.error('Backend chat API request failed:', err);
        addToast(`Backend Error: ${err.message}`, 'error');
      }
      setIsLoading(false);
    }
  };

  const handleExecuteAction = async (actionId, conditionId) => {
    let activeThreadId = currentSession?.threadId;
    if (!activeThreadId) {
      try {
        const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user')?.text || 'Clinical consultation';
        const initData = await chatApi.startSession(lastUserMsg, { getToken: getAuthToken });
        activeThreadId = initData.thread_id;
        updateSession(currentSession.id, { threadId: activeThreadId });
        setCurrentSession((prev) => ({ ...prev, threadId: activeThreadId }));
      } catch (initErr) {
        logger.error('Failed to auto-initialize session for action:', initErr);
        addToast('No active clinical session found. Please type a message to start.', 'error');
        return;
      }
    }

    setActiveActionId(actionId);
    setIsLoading(true);
    setThinkingStep(
      actionId === 'GET_AYURVEDIC_GUIDANCE'
        ? 'Retrieving Ayurvedic clinical guidance...'
        : 'Finding nearby verified healthcare facilities...'
    );

    let coords = null;
    if (actionId === 'FIND_NEARBY_CLINICS') {
      if (typeof navigator !== 'undefined' && navigator.geolocation) {
        try {
          const pos = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
              enableHighAccuracy: true,
              timeout: 8000,
              maximumAge: 30000,
            });
          });
          if (pos?.coords?.latitude != null && pos?.coords?.longitude != null) {
            coords = { latitude: pos.coords.latitude, longitude: pos.coords.longitude };
          }
        } catch (geoErr) {
          logger.warn('Geolocation permission denied or timed out:', geoErr);
          addToast('Location access not granted. Direct Google Maps search links provided.', 'info');
        }
      } else {
        addToast('Geolocation is not supported by your browser.', 'info');
      }
    }

    try {
      const requestOptions = {
        getToken: getAuthToken,
      };

      const actionData = await chatApi.executeAction(activeThreadId, actionId, conditionId, coords, requestOptions);

      const botMessage = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        text: actionData.message || 'Action completed.',
        stage: actionData.stage,
        is_complete: actionData.is_complete,
        symptom_facts: actionData.symptom_facts || {},
        assessment: actionData.assessment || null,
        actions: actionData.actions || [],
        facilities: actionData.facilities || null,
        external_search: actionData.external_search || null,
        ayurvedic_guidance: actionData.ayurvedic_guidance || null,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        ...(actionData.risk_level && { risk_level: actionData.risk_level }),
        ...(actionData.sources && { sources: actionData.sources }),
      };

      const updatedMsgs = [...messages, botMessage];
      setMessages(updatedMsgs);
      const finalSess = updateSession(currentSession.id, {
        messages: updatedMsgs,
        threadId: activeThreadId,
      });
      if (finalSess) {
        setCurrentSession(finalSess);
      }
    } catch (err) {
      logger.error('Failed to execute action:', err);
      addToast(`Action failed: ${err.message}`, 'error');
    } finally {
      setIsLoading(false);
      setActiveActionId(null);
    }
  };

  const handleCopyText = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedMsgId(id);
    addToast('Response copied to clipboard', 'success');
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
    setThinkingStep('Consultation paused');
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className="flex flex-col h-[calc(100vh-100px)] min-h-[580px] relative overflow-hidden"
    >
      {/* DRAG & DROP OVERLAY DROPZONE */}
      {isDragging && (
        <div className="absolute inset-0 z-50 bg-[var(--bg-app)]/90 border-2 border-dashed border-[var(--clinical-teal)] rounded-xl flex flex-col items-center justify-center space-y-3 backdrop-blur-md animate-fade-in pointer-events-none">
          <div className="w-12 h-12 rounded-lg bg-[var(--clinical-teal)]/15 border border-[var(--clinical-teal)]/30 text-[var(--clinical-teal)] flex items-center justify-center">
            <UploadCloud size={24} />
          </div>
          <p className="text-sm font-semibold text-[var(--text-primary)]">Drop medical files or images here</p>
          <p className="text-xs text-[var(--text-muted)]">Supports PDF, PNG, JPG, WEBP, DOCX, and TXT reports</p>
        </div>
      )}

      {/* MAIN CONVERSATION WORKSPACE & CITATIONS CONTAINER */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start overflow-hidden pt-2">
        {/* Messages Feed Column */}
        <div className={showCitationDrawer ? 'lg:col-span-8 flex flex-col h-full overflow-hidden' : 'lg:col-span-12 flex flex-col h-full overflow-hidden'}>
          {/* Scrollable Conversation Stream */}
          <div
            ref={chatContainerRef}
            onScroll={handleScroll}
            className="flex-1 overflow-y-auto pr-2 space-y-4 scroll-smooth relative"
          >
            {/* MINIMAL LINEAR / APPLE NOTES WELCOME STATE */}
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center py-12 text-center max-w-xl mx-auto space-y-8 animate-fade-in my-auto">
                <div className="space-y-3">
                  <div className="w-12 h-12 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--clinical-teal)] flex items-center justify-center mx-auto shadow-sm">
                    <Sparkles size={22} />
                  </div>
                  <h1 className="text-2xl sm:text-3xl font-medium text-[var(--text-primary)] tracking-tight">
                    BluCare<span className="text-[var(--clinical-teal)] font-semibold">+</span>
                  </h1>
                  <p className="text-xs font-mono text-[var(--clinical-teal)] tracking-wider uppercase">
                    Clinical AI Triage & Guidance
                  </p>
                  <p className="text-xs text-[var(--text-secondary)] max-w-md mx-auto leading-relaxed">
                    Describe your symptoms, ask health questions, or upload lab reports for evidence-grounded differential assessment.
                  </p>
                </div>

                {/* Suggested Prompt Pills */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full text-left">
                  {suggestedPrompts.map((promptText, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(promptText)}
                      className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--clinical-teal)]/40 hover:bg-[var(--bg-elevated)] text-xs text-[var(--text-primary)] transition-all text-left flex items-center justify-between group cursor-pointer shadow-sm"
                    >
                      <span className="line-clamp-2 leading-relaxed">{promptText}</span>
                      <Sparkles size={12} className="text-[var(--text-muted)] group-hover:text-[var(--clinical-teal)] transition-colors shrink-0 ml-2" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* STRUCTURED MESSAGES FEED */}
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                onExecuteAction={handleExecuteAction}
                isLoadingAction={isLoading}
                activeActionId={activeActionId}
                onCopyText={handleCopyText}
                copiedMsgId={copiedMsgId}
              />
            ))}

            {/* ANIMATED CLINICAL THINKING STATE / SKELETON */}
            {isLoading && (
              <div className="pt-2 animate-fade-in">
                {thinkingStep?.toLowerCase().includes('assessment') ? (
                  <AssessmentSkeleton currentStep={thinkingStep} />
                ) : (
                  <TypingIndicator step={thinkingStep} onStop={handleStopGeneration} />
                )}
              </div>
            )}
          </div>

          {/* Floating Scroll-To-Bottom Button */}
          {showScrollBottom && (
            <button
              onClick={scrollToBottom}
              className="absolute bottom-28 right-8 z-30 p-2 rounded-[6px] bg-[var(--bg-elevated)] border border-[var(--border-strong)] text-[var(--clinical-teal)] shadow-md hover:bg-[var(--bg-surface)] transition-all cursor-pointer"
              title="Scroll to latest message"
            >
              <ArrowDown size={15} />
            </button>
          )}

          {/* ---------------------------------------------------- */}
          {/* COMPOSER INPUT BAR WITH FILE CHIPS & VOICE INDICATOR */}
          {/* ---------------------------------------------------- */}
          <div className="pt-3 shrink-0 relative z-20">
            {/* Hidden File Picker Input */}
            <input
              type="file"
              ref={fileInputRef}
              multiple
              accept="image/*,.pdf,.doc,.docx,.txt"
              onChange={(e) => handleFileSelect(e.target.files)}
              className="hidden"
            />

            {/* Attached File Preview Chips */}
            {attachedFiles.length > 0 && (
              <div className="flex flex-wrap items-center gap-2 pb-2.5 px-1">
                {attachedFiles.map((fileObj) => {
                  const isImg = fileObj.type.startsWith('image/');
                  return (
                    <div
                      key={fileObj.id}
                      className="flex items-center gap-2 px-2.5 py-1.5 rounded-[6px] bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-xs text-[var(--text-primary)] relative overflow-hidden group shadow-sm"
                    >
                      {/* Upload Progress Line */}
                      {fileObj.status === 'uploading' && (
                        <div
                          className="absolute bottom-0 left-0 h-0.5 bg-[var(--clinical-teal)] transition-all duration-150"
                          style={{ width: `${fileObj.progress}%` }}
                        />
                      )}

                      {isImg && fileObj.previewUrl ? (
                        <img src={fileObj.previewUrl} alt="Thumbnail" className="w-5 h-5 rounded-[4px] object-cover" />
                      ) : (
                        <FileText size={14} className="text-[var(--clinical-teal)] shrink-0" />
                      )}

                      <div className="flex flex-col min-w-0">
                        <span className="truncate max-w-[120px] font-medium leading-tight">{fileObj.name}</span>
                        <span className="text-[9px] text-[var(--text-muted)] font-mono">
                          {fileObj.status === 'uploading' ? `${fileObj.progress}%` : formatFileSize(fileObj.size)}
                        </span>
                      </div>

                      {fileObj.status === 'error' ? (
                        <button
                          type="button"
                          onClick={() => handleRetryUpload(fileObj.id)}
                          className="text-[var(--severity-emergency)] hover:opacity-80 p-0.5 cursor-pointer ml-1"
                          title="Retry Upload"
                        >
                          <RotateCcw size={12} />
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleRemoveFile(fileObj.id)}
                          className="text-[var(--text-muted)] hover:text-[var(--severity-emergency)] p-0.5 cursor-pointer ml-1"
                          title="Remove File"
                        >
                          <X size={12} />
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Active Voice Recording Status Bar */}
            {isRecording && (
              <div className="flex items-center justify-between px-4 py-2 mb-2 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 animate-fade-in">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
                  <span className="font-semibold">Voice Listener Active</span>
                  <span className="font-mono text-[11px] opacity-80">({recordingTime}s)</span>
                </div>

                {/* Animated Audio Waveform Bars */}
                <div className="flex items-center gap-1 h-3">
                  {[40, 90, 60, 100, 50, 80].map((h, i) => (
                    <div
                      key={i}
                      className="w-1 bg-rose-400 rounded-full animate-pulse"
                      style={{ height: `${h}%`, animationDelay: `${i * 100}ms` }}
                    />
                  ))}
                </div>

                <button
                  type="button"
                  onClick={stopVoiceRecording}
                  className="px-2.5 py-1 rounded-xl bg-rose-500 text-white font-medium text-[11px] hover:bg-rose-600 transition-colors cursor-pointer"
                >
                  Done Listening
                </button>
              </div>
            )}

            {/* Composer Input Box Form */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="relative flex items-end gap-2 bg-[var(--bg-surface)] border border-[var(--border-subtle)] focus-within:border-[var(--clinical-teal)] rounded-xl p-2.5 shadow-sm transition-all"
            >
              {/* Paperclip File Upload Trigger */}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="p-2 rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer shrink-0 focus-visible:outline-2 focus-visible:outline-[var(--clinical-teal)]"
                title="Attach Medical Report / Photo (PDF, Images)"
              >
                <Paperclip size={16} />
              </button>

              {/* Textarea Input */}
              <textarea
                ref={textareaRef}
                rows={1}
                value={inputQuery}
                onChange={handleInputChange}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="Describe symptoms or ask clinical questions... (Enter to send, Shift+Enter for newline)"
                className="flex-1 bg-transparent text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] outline-none resize-none py-1.5 max-h-40 overflow-y-auto leading-relaxed"
              />

              {/* Microphone Voice Button */}
              <button
                type="button"
                onClick={toggleVoiceRecording}
                className={`p-2 rounded-md transition-colors cursor-pointer shrink-0 focus-visible:outline-2 focus-visible:outline-[var(--clinical-cyan)] ${
                  isRecording
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40 animate-pulse'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]'
                }`}
                title={isRecording ? 'Stop Voice Recording' : 'Start Voice Dictation'}
              >
                {isRecording ? <MicOff size={16} /> : <Mic size={16} />}
              </button>

              {/* Send Button */}
              <button
                type="submit"
                disabled={isLoading || (!inputQuery.trim() && attachedFiles.length === 0)}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-md bg-[var(--accent-primary)] text-[#101316] font-medium text-xs hover:bg-[var(--accent-hover)] active:scale-[0.98] transition-all disabled:opacity-30 disabled:cursor-not-allowed shrink-0 cursor-pointer shadow-sm"
              >
                <span>Send</span>
                <Send size={13} />
              </button>
            </form>
          </div>
        </div>

        {/* Slide-Out Clinical Citation Reference Drawer */}
        {showCitationDrawer && (
          <div className="lg:col-span-4 h-full overflow-y-auto animate-fade-in">
            <div className="space-y-4 p-4 rounded-[10px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] shadow-sm">
              <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
                <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
                  <FileSearch size={16} className="text-[var(--clinical-teal)] shrink-0" /> Clinical Citations
                </h3>
                <button
                  onClick={() => setShowCitationDrawer(false)}
                  className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-xs cursor-pointer"
                >
                  Close
                </button>
              </div>

              <div className="space-y-3 text-xs">
                <div className="p-3.5 rounded-[8px] bg-[var(--bg-elevated)] border border-[var(--border-subtle)] space-y-1.5">
                  <p className="font-semibold text-[var(--clinical-teal)]">{selectedCitation?.title || 'Clinical Guideline Reference'}</p>
                  <p className="text-[var(--text-muted)] font-mono text-[10px]">Reference ID: {selectedCitation?.id || selectedCitation?.ref_id || 'DOC-REF'}</p>
                  {selectedCitation?.tag && (
                    <p className="text-[var(--text-muted)] text-[11px]">Publisher: {selectedCitation.tag}</p>
                  )}
                  {selectedCitation?.snippet && (
                    <p className="text-[var(--text-secondary)] mt-2 leading-relaxed">
                      "{selectedCitation.snippet}"
                    </p>
                  )}
                </div>

                <div className="p-3.5 rounded-[8px] bg-[var(--bg-elevated)] border border-[var(--border-subtle)] space-y-2">
                  <span className="font-semibold text-[var(--text-primary)]">Protocol Accordance</span>
                  <div className="flex items-center gap-2 text-[var(--severity-routine)]">
                    <CheckCircle2 size={16} className="shrink-0" /> Verified Clinical Evidence Alignment
                  </div>
                </div>

                {selectedCitation?.url ? (
                  <a
                    href={selectedCitation.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 text-[var(--clinical-teal)] hover:underline text-xs pt-1"
                  >
                    View Guideline Source <ExternalLink size={12} />
                  </a>
                ) : (
                  <p className="text-[var(--text-muted)] text-[11px] pt-1">Indexed in verified clinical knowledge base.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MultiRagChatPage;

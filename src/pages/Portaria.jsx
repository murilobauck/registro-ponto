// src/pages/Portaria.jsx

import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import 'boxicons/css/boxicons.min.css';
import styles from './Portaria.module.css'; // Importa o CSS Module, que está correto.

const API_BASE_URL = "https://annette-seminomadic-arctically.ngrok-free.dev";

// --- Componente Modal ---
// A correção está aqui: usamos os nomes de classe globais diretamente.
function RecognitionModal({ isOpen, onClose, onCaptureSuccess }) {
  const [status, setStatus] = useState({ message: 'Posicione seu rosto no centro.', type: 'info' });
  const [isLoading, setIsLoading] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const activeStream = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setStatus({ message: 'Posicione seu rosto no centro.', type: 'info' });
      setIsLoading(false);
      startCamera();
    } else {
      stopCamera();
    }
    return () => stopCamera();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const startCamera = async () => {
    try {
      if (activeStream.current) activeStream.current.getTracks().forEach(track => track.stop());
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) videoRef.current.srcObject = stream;
      activeStream.current = stream;
    } catch (err) {
      setStatus({ message: 'Não foi possível acessar a câmera.', type: 'error' });
    }
  };
  
  const stopCamera = () => {
    if (activeStream.current) {
        activeStream.current.getTracks().forEach(track => track.stop());
        activeStream.current = null;
    }
    if (videoRef.current && videoRef.current.srcObject) videoRef.current.srcObject = null;
  };

  const handleCapture = async (event) => {
    event.stopPropagation();
    setIsLoading(true);
    setStatus({ message: 'Processando reconhecimento...', type: 'info' });
    
    const canvas = canvasRef.current;
    const video = videoRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    context.translate(canvas.width, 0);
    context.scale(-1, 1);
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob(async (blob) => {
        if (!blob) {
            setStatus({ message: 'Erro ao capturar imagem.', type: 'error' });
            setIsLoading(false);
            return;
        }
        const formData = new FormData();
        formData.append("imagem", blob, "ponto.jpg");
        try {
            const response = await fetch(`${API_BASE_URL}/registrar-ponto`, { method: "POST", body: formData });
            const data = await response.json();
            if (data.sucesso) {
                onCaptureSuccess(data.mensagem);
                setTimeout(onClose, 2000);
            } else {
                setStatus({ message: data.mensagem, type: "error" });
                setIsLoading(false);
            }
        } catch (error) {
            setStatus({ message: 'Erro de comunicação. Tente novamente.', type: 'error' });
            setIsLoading(false);
        }
    }, "image/jpeg");
  };

  if (!isOpen) return null;

  return (
    // CORREÇÃO: Usando "modal-backdrop" como string, pois é uma classe global do index.css
    <div className="modal-backdrop" onClick={onClose} style={{ display: isOpen ? 'flex' : 'none' }}>
      {/* CORREÇÃO: Usando "modal-content" como string */}
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Registro de Ponto Facial</h3>
          <button type="button" className="close-btn" onClick={onClose}>&times;</button>
        </div>
        <div className="modal-body">
          <div className="camera-feed" style={{ display: isLoading ? 'none' : 'block' }}>
            <video ref={videoRef} autoPlay playsInline></video>
            <canvas ref={canvasRef} style={{display: 'none'}}></canvas>
          </div>
          <div className={`status-message status-${status.type} ${isLoading ? 'loading' : ''}`}>
            {isLoading && <div className="loader"></div>}
            <div>{status.message}</div>
          </div>
          <button type="button" className="btn" onClick={handleCapture} disabled={isLoading} style={{ width: '100%' }}>
            <i className="bx bxs-camera"></i> Capturar e Identificar
          </button>
        </div>
      </div>
    </div>
  );
}

// --- Componente da Página da Portaria ---
function Portaria() {
  const [time, setTime] = useState(new Date());
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [mainStatus, setMainStatus] = useState({ message: '', type: '' });

  useEffect(() => {
    const timerId = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timerId);
  }, []);

  const handleCaptureSuccess = (message) => {
    setMainStatus({ message, type: 'success' });
    setTimeout(() => setMainStatus({ message: '', type: '' }), 4000);
  };

  const dateOptions = { weekday: "long", year: "numeric", month: "long", day: "numeric" };
  
  return (
    // CORREÇÃO: Aqui usamos o styles.portariaContainer, pois ele vem do Portaria.module.css
    <div className={styles.portariaContainer}>
      <main id="portaria-view" className={`card ${styles.portariaCard}`}>
        <i className={`bx bx-time-five ${styles.clockIcon}`}></i>
        <div className={styles.timeDisplay}>{time.toLocaleTimeString("pt-BR")}</div>
        <div className={styles.dateDisplay}>{time.toLocaleDateString("pt-BR", dateOptions)}</div>
        <button type="button" className="btn" onClick={() => setIsModalOpen(true)}>
          <i className="bx bx-camera"></i> Registrar Ponto
        </button>
        {mainStatus.message && (
          <div className={`status-message status-${mainStatus.type}`} style={{marginTop: '20px'}}>
            {mainStatus.message}
          </div>
        )}
        <div className={styles.linkRh}>
          <Link to="/rh">Acessar Área de RH</Link>
        </div>
      </main>

      <RecognitionModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)}
        onCaptureSuccess={handleCaptureSuccess}
      />
    </div>
  );
}

export default Portaria;
import React, { useState, useEffect, useMemo, useRef } from "react";
import { Link } from "react-router-dom";
import "boxicons/css/boxicons.min.css";
import styles from "./Rh.module.css";

const DEPARTAMENTOS = [
  "Diretoria/Executivo",
  "Administrativo e Financeiro",
  "Recursos Humanos",
  "Marketing e Vendas",
  "Operações",
  "Tecnologia da Informação (TI)",
  "Jurídico e Compliance",
  "Atendimento ao Cliente",
  "Pesquisa e Desenvolvimento (P&D)",
];

const API_BASE_URL = "https://registro-ponto-bosch.vercel.app";

function GestaoView({ onAddNew }) {
  const [funcionarios, setFuncionarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  const [stats, setStats] = useState({
    total: 0,
    ativos: 0,
    inativos: 0,
    departamentos: 0,
  });

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const [funcResponse, statsResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/funcionarios`, {
            headers: { "ngrok-skip-browser-warning": "true" },
          }),
          fetch(`${API_BASE_URL}/stats`, {
            headers: { "ngrok-skip-browser-warning": "true" },
          }),
        ]);

        if (!funcResponse.ok) throw new Error("Falha ao buscar funcionários");
        if (!statsResponse.ok) throw new Error("Falha ao buscar estatísticas");

        const funcData = await funcResponse.json();
        const statsData = await statsResponse.json();

        setFuncionarios(funcData);
        setStats(statsData);
      } catch (error) {
        console.error("Erro ao buscar dados:", error);
        alert("Não foi possível carregar os dados do RH.");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [refreshKey]);

  useEffect(() => {
    async function fetchFuncionarios() {
      setLoading(true);
      try {
        const response = await fetch(`${API_BASE_URL}/funcionarios`, {
          headers: {
            "ngrok-skip-browser-warning": "true",
          },
        });

        if (!response.ok) throw new Error("Falha ao buscar dados");
        const data = await response.json();
        setFuncionarios(data);
      } catch (error) {
        console.error("Erro ao buscar funcionários:", error);
        alert("Não foi possível carregar a lista de funcionários.");
      } finally {
        setLoading(false);
      }
    }
    fetchFuncionarios();
  }, [refreshKey]);

  const filteredFuncionarios = useMemo(
    () =>
      funcionarios.filter(
        (func) =>
          func.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (func.departamento &&
            func.departamento
              .toLowerCase()
              .includes(searchTerm.toLowerCase())) ||
          func.id.toString().includes(searchTerm)
      ),
    [funcionarios, searchTerm]
  );

  const handleDelete = async (id, nome) => {
    if (!confirm(`Tem certeza que deseja remover "${nome}" (ID: ${id})?`))
      return;
    try {
      const response = await fetch(
        `${API_BASE_URL}/remover-funcionario/${id}`,
        { method: "DELETE" }
      );
      const data = await response.json();
      alert(data.mensagem);
      if (data.sucesso) {
        setRefreshKey((oldKey) => oldKey + 1);
      }
    } catch (error) {
      alert("Erro de comunicação ao tentar remover.");
    }
  };

  return (
    <>
      <header className={styles.mainHeader}>
        <div>
          <h2 className={styles.title}>Gestão de Funcionários</h2>
          <p className={styles.subtitle}>
            Visualize, edite e gerencie informações dos colaboradores
          </p>
        </div>
      </header>

      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={styles.statCardInfo}>
            <div className={styles.value}>{stats.total}</div>
            <div className={styles.label}>Total</div>
          </div>
          <i className={`bx bx-group ${styles.statCardIcon}`}></i>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statCardInfo}>
            <div className={styles.value}>{stats.ativos}</div>
            <div className={styles.label}>Ativos</div>
          </div>
          <i
            className={`bx bx-check-circle ${styles.statCardIcon}`}
            style={{ color: "var(--success-color)" }}
          ></i>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statCardInfo}>
            <div className={styles.value}>{stats.inativos}</div>
            <div className={styles.label}>Inativos</div>
          </div>
          <i className={`bx bx-x-circle ${styles.statCardIcon}`}></i>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statCardInfo}>
            <div className={styles.value}>{stats.departamentos}</div>
            <div className={styles.label}>Departamentos</div>
          </div>
          <i className={`bx bx-filter-alt ${styles.statCardIcon}`}></i>
        </div>
      </div>

      <div className="card">
        <div className={styles.tableToolbar}>
          <h3>Lista de Funcionários</h3>
          <div className={styles.toolbarActions}>
            <input
              type="text"
              className={styles.searchBox}
              placeholder="Buscar por nome, ID ou departamento..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <button className="btn" onClick={onAddNew}>
              <i className="bx bx-plus"></i> Novo Funcionário
            </button>
          </div>
        </div>
        {loading ? (
          <p style={{ textAlign: "center", padding: "20px" }}>Carregando...</p>
        ) : (
          <div className={styles.tableResponsive}>
            <table className={styles.dataTable}>
              <thead>
                <tr>
                  <th>Funcionário</th>
                  <th>Departamento</th>
                  <th>Cargo</th>
                  <th>Status</th>
                  <th>Admissão</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {filteredFuncionarios.length > 0 ? (
                  filteredFuncionarios.map((func) => (
                    <tr key={func.id}>
                      <td>
                        <div className={styles.employeeCell}>
                          <div className={styles.avatarSm}>
                            {func.nome
                              .split(" ")
                              .map((n) => n[0])
                              .join("")
                              .substring(0, 2)
                              .toUpperCase()}
                          </div>
                          <div>
                            <strong>{func.nome}</strong>
                            <br />
                            <small>ID: {func.id}</small>
                          </div>
                        </div>
                      </td>
                      <td>{func.departamento}</td>
                      <td>{func.cargo}</td>
                      <td>
                        <span
                          className={`${styles.statusBadge} ${
                            func.status
                              ? styles[func.status.toLowerCase()]
                              : styles.inativo
                          }`}
                        >
                          {func.status || "N/A"}
                        </span>
                      </td>
                      <td>{func.admissao}</td>
                      <td className={styles.actionButtons}>
                        <a
                          title="Remover"
                          onClick={() => handleDelete(func.id, func.nome)}
                        >
                          <i className="bx bx-trash"></i>
                        </a>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan="6"
                      style={{ textAlign: "center", padding: "40px" }}
                    >
                      Nenhum funcionário encontrado.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}

function CadastroView({ onCancel, onCadastroComplete }) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    nome: "",
    departamento: "",
    cargo: "",
  });
  const [capturedBlob, setCapturedBlob] = useState(null);
  const [status, setStatus] = useState({ message: "", type: "info" });
  const [isLoading, setIsLoading] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const activeStream = useRef(null);

  useEffect(() => {
    if (step === 2) {
      startCamera();
    } else {
      stopCamera();
    }
  }, [step]);

  const handleInputChange = (e) => {
    const { id, value } = e.target;
    setFormData((prev) => ({ ...prev, [id]: value }));
  };

  const startCamera = async () => {
    try {
      if (activeStream.current)
        activeStream.current.getTracks().forEach((track) => track.stop());
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) videoRef.current.srcObject = stream;
      activeStream.current = stream;
    } catch (err) {
      setStatus({
        message: "Não foi possível acessar a câmera.",
        type: "error",
      });
    }
  };

  const stopCamera = () => {
    if (activeStream.current) {
      activeStream.current.getTracks().forEach((track) => track.stop());
      activeStream.current = null;
    }
    if (videoRef.current && videoRef.current.srcObject)
      videoRef.current.srcObject = null;
  };

  const handleCapture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    context.translate(canvas.width, 0);
    context.scale(-1, 1);
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => setCapturedBlob(blob), "image/jpeg");
    setStep(3);
  };

  const handleSubmit = async () => {
    if (
      !formData.nome ||
      !formData.departamento ||
      !formData.cargo ||
      !capturedBlob
    ) {
      setStatus({
        message: "Dados ou foto ausentes. Verifique os passos.",
        type: "error",
      });
      return;
    }
    setIsLoading(true);
    setStatus({ message: "Enviando dados para cadastro...", type: "info" });

    const submissionData = new FormData();
    submissionData.append("nome", formData.nome);
    submissionData.append("departamento", formData.departamento);
    submissionData.append("cargo", formData.cargo);
    submissionData.append("imagem", capturedBlob, "cadastro.jpg");

    try {
      const response = await fetch(`${API_BASE_URL}/cadastrar`, {
        method: "POST",
        body: submissionData,
      });
      const data = await response.json();
      if (data.sucesso) {
        setStatus({
          message: `${data.mensagem} Novo ID: ${data.id_gerado}`,
          type: "success",
        });
        setTimeout(() => onCadastroComplete(), 2000);
      } else {
        setStatus({ message: data.erro || data.mensagem, type: "error" });
        setIsLoading(false);
      }
    } catch (error) {
      setStatus({
        message: "Erro de comunicação com o servidor.",
        type: "error",
      });
      setIsLoading(false);
    }
  };

  const goToStep = (stepNumber) => {
    setStep(stepNumber);
  };

  return (
    <div className="card">
      <header className={styles.mainHeader}>
        <div>
          <h2 className={styles.title}>Novo Funcionário</h2>
          <p className={styles.subtitle}>
            Siga os passos para adicionar um novo colaborador
          </p>
        </div>
      </header>

      <div style={{ display: step === 1 ? "block" : "none" }}>
        <h4 style={{ marginBottom: "1rem" }}>Dados Pessoais</h4>
        <div className={styles.formGroup}>
          <label>Nome Completo</label>
          <input
            type="text"
            id="nome"
            value={formData.nome}
            onChange={handleInputChange}
          />
        </div>
        <div className={styles.formGroup}>
          <label>Departamento</label>
          <select
            id="departamento"
            value={formData.departamento}
            onChange={handleInputChange}
          >
            <option value="" disabled>
              Selecione um departamento...
            </option>

            {DEPARTAMENTOS.map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}
          </select>
        </div>
        <div className={styles.formGroup}>
          <label>Cargo</label>
          <input
            type="text"
            id="cargo"
            value={formData.cargo}
            onChange={handleInputChange}
          />
        </div>
        <div className={styles.wizardButtons}>
          <button className="btn btn-danger" onClick={onCancel}>
            Cancelar
          </button>
          <button className="btn" onClick={() => goToStep(2)}>
            Próximo
          </button>
        </div>
      </div>

      <div style={{ display: step === 2 ? "block" : "none" }}>
        <h4>Captura Facial</h4>
        <div className={styles.cameraContainer}>
          <div className="camera-feed">
            <video ref={videoRef} autoPlay playsInline></video>
            <canvas ref={canvasRef} style={{ display: "none" }}></canvas>
          </div>
        </div>
        <div className={styles.wizardButtons}>
          <button className="btn" onClick={() => goToStep(1)}>
            Anterior
          </button>
          <button className="btn" onClick={handleCapture}>
            Tirar Foto
          </button>
        </div>
      </div>

      <div style={{ display: step === 3 ? "block" : "none" }}>
        <h4>Confirmação</h4>
        <div className={styles.cameraContainer}>
          {capturedBlob && (
            <img
              src={URL.createObjectURL(capturedBlob)}
              alt="Preview"
              className={styles.capturePreview}
            />
          )}
        </div>
        <div className={styles.wizardButtons}>
          <button className="btn" onClick={() => goToStep(2)}>
            Tirar Nova Foto
          </button>
          <button
            className="btn btn-success"
            onClick={handleSubmit}
            disabled={isLoading}
          >
            {isLoading ? "Salvando..." : "Salvar Cadastro"}
          </button>
        </div>
      </div>

      {status.message && (
        <div
          className={`status-message status-${status.type}`}
          style={{ marginTop: "20px" }}
        >
          {status.message}
        </div>
      )}
    </div>
  );
}

function Rh() {
  const [view, setView] = useState("list");
  const [refreshKey, setRefreshKey] = useState(0);

  const handleCadastroComplete = () => {
    setRefreshKey((oldKey) => oldKey + 1);
    setView("list");
  };

  return (
    <div className={styles.rhContainer}>
      {view === "list" ? (
        <GestaoView onAddNew={() => setView("cadastro")} />
      ) : (
        <CadastroView
          onCancel={() => setView("list")}
          onCadastroComplete={handleCadastroComplete}
        />
      )}

      <div
        style={{ marginTop: "40px", fontSize: "0.9em", textAlign: "center" }}
      >
        <Link to="/" style={{ color: "var(--text-muted)" }}>
          Voltar para Portaria
        </Link>
      </div>
    </div>
  );
}

export default Rh;

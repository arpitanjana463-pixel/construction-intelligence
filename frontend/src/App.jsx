
import { useState, useRef } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState("");
  const [imageCount, setImageCount] = useState(0);

  const requestInProgress = useRef(false);

  const API_URL = "https://construction-intelligence-boxq.onrender.com/analyze-image";

  function handleUpload(event) {
    const selectedFile = event.target.files?.[0];

    if (!selectedFile) return;

    const allowedTypes = ["image/jpeg", "image/png", "image/webp"];

    if (!allowedTypes.includes(selectedFile.type)) {
      setFile(null);
      setAnalysis("");
      setMessage("Please select a JPG, PNG, or WEBP image.");
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setFile(null);
      setAnalysis("");
      setMessage("Image must be smaller than 10 MB.");
      return;
    }

    setFile(selectedFile);
    setMessage("");
    setAnalysis("");
  }

  async function analyzeImage() {
    if (requestInProgress.current) return;

    if (!file) {
      setMessage("Please select a construction site image first.");
      return;
    }

    requestInProgress.current = true;
    setLoading(true);
    setMessage("Uploading image and analyzing with AI...");
    setAnalysis("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      console.log("API URL:", API_URL);

      const response = await fetch(API_URL, {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        if (response.status === 429) {
          setMessage(
            result.message ||
            "Gemini API daily quota exceeded. Please try after quota reset."
          );
        } else if (response.status === 503) {
          setMessage(
            "Gemini AI is temporarily busy. Please try again later."
          );
        } else {
          setMessage(result.message || "Image analysis failed.");
        }

        return;
      }

      setAnalysis(result.analysis || "");
      setImageCount((previous) => previous + 1);
      setMessage(
        `AI analysis completed successfully for ${result.filename || file.name}.`
      );

    } catch (error) {
      console.error("Analysis error:", error);

      setMessage(
        "Cannot connect to the backend. Please check that FastAPI is running."
      );

    } finally {
      requestInProgress.current = false;
      setLoading(false);
    }
  }

  function removeImage() {
    if (loading) return;

    setFile(null);
    setMessage("");
    setAnalysis("");
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <h2>
          Build<span>AI</span>
        </h2>

        <p className="side-label">WORKSPACE</p>

        <a className="nav-item active" href="#dashboard">
          ▦ Dashboard
        </a>
        <a className="nav-item" href="#analysis">
          ▧ Site Analysis
        </a>
        <a className="nav-item" href="#safety">
          ♧ Worker Safety
        </a>
        <a className="nav-item" href="#planning">
          ⌂ Project Planning
        </a>

        <div className="sidebar-bottom">
          Construction Intelligence
          <br />
          Platform v1.0
        </div>
      </aside>

      <main className="main" id="dashboard">
        <header className="topbar">
          <div>
            <p className="eyebrow">CONSTRUCTION INTELLIGENCE</p>
            <h1>Project Dashboard</h1>
          </div>

          <div className="status">
            <span />
            System Online
          </div>
        </header>

        <section className="welcome">
          <div>
            <p className="eyebrow">SMART CONSTRUCTION PLATFORM</p>
            <h2>Build smarter with AI.</h2>
            <p>
              Analyze site images, monitor safety, and plan construction
              in one place.
            </p>
          </div>

          <div className="welcome-icon">⌂</div>
        </section>

        <section className="stats">
          <div className="stat-card">
            <span className="stat-icon">▦</span>
            <p>Site Images Analyzed</p>
            <h2>{imageCount}</h2>
            <small>Successful analyses in this session</small>
          </div>

          <div className="stat-card">
            <span className="stat-icon">♧</span>
            <p>Safety Checks</p>
            <h2>{imageCount}</h2>
            <small>Image-based safety reviews completed</small>
          </div>

          <div className="stat-card">
            <span className="stat-icon">⌂</span>
            <p>Project Plans</p>
            <h2>0</h2>
            <small>Start planning your project</small>
          </div>
        </section>

        <section className="content-grid">
          <div className="panel upload-panel" id="analysis">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">COMPUTER VISION</p>
                <h2>Construction Site Analysis</h2>
              </div>

              <span className="tag">IMAGE AI</span>
            </div>

            <label className="upload-area">
              <span className="upload-icon">↑</span>
              <strong>Upload a construction image</strong>
              <span>Click to browse your computer</span>
              <small>JPG, PNG or WEBP · Maximum 10 MB</small>

              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={handleUpload}
                disabled={loading}
              />
            </label>

            {file && (
              <div className="selected-file">
                <span>▧</span>

                <div>
                  <strong>{file.name}</strong>
                  <small>{(file.size / 1024).toFixed(1)} KB</small>
                </div>

                <button
                  type="button"
                  className="remove-button"
                  onClick={removeImage}
                  disabled={loading}
                >
                  Remove
                </button>
              </div>
            )}

            <button
              type="button"
              className="primary-button"
              onClick={analyzeImage}
              disabled={loading || !file}
            >
              {loading ? "Analyzing..." : "Analyze Site Image →"}
            </button>

            {message && (
              <p
                role="status"
                aria-live="polite"
                style={{
                  marginTop: "14px",
                  lineHeight: 1.6,
                  color: message.includes("successfully")
                    ? "green"
                    : loading
                      ? "#555"
                      : "#c0392b",
                }}
              >
                {message}
              </p>
            )}

            {analysis && (
              <div className="panel" style={{ marginTop: "16px" }}>
                <h2>AI Analysis Results</h2>

                <p style={{ whiteSpace: "pre-wrap", lineHeight: 1.7 }}>
                  {analysis}
                </p>
              </div>
            )}
          </div>

          <div className="panel insights-panel">
            <p className="eyebrow">PLATFORM MODULES</p>
            <h2>Intelligence Center</h2>

            <div className="module">
              <div className="module-icon purple">▧</div>
              <div>
                <strong>Site Image Analysis</strong>
                <p>Upload and validate construction images.</p>
              </div>
              <span>01</span>
            </div>

            <div className="module" id="safety">
              <div className="module-icon orange">♧</div>
              <div>
                <strong>Worker Safety</strong>
                <p>Safety monitoring module coming next.</p>
              </div>
              <span>02</span>
            </div>

            <div className="module" id="planning">
              <div className="module-icon green">⌂</div>
              <div>
                <strong>Material &amp; Planning</strong>
                <p>Construction estimates and project planning.</p>
              </div>
              <span>03</span>
            </div>

            <div className="notice">
              <strong>Next milestone</strong>
              <p>
                Connect an AI model to analyze construction images
                and generate useful findings.
              </p>
            </div>
          </div>
        </section>

        <footer>
          BuildAI · Multimodal Construction Intelligence Platform
        </footer>
      </main>
    </div>
  );
}

export default App;

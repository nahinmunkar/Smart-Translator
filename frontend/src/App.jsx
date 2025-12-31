import { useState } from 'react';
import './App.css';

function App() {
  const [inputText, setInputText] = useState('');
  const [targetLang, setTargetLang] = useState('English'); // Default target
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showAllMode, setShowAllMode] = useState(false);

  // Helper: Detect if text contains Arabic characters
  const isArabic = (text) => /[\u0600-\u06FF]/.test(text);

  const handleTranslate = async () => {
    setLoading(true);
    setError(null);
    setData(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Now we send the selected target language instead of hardcoded French
        body: JSON.stringify({ text: inputText, target_lang: targetLang }),
      });

      if (!response.ok) {
        const result = await response.json();
        throw new Error(result.detail || "Translation failed");
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error("Error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Determine if we should use Right-to-Left layout
  const isRTL = isArabic(inputText);

  return (
    <div className="container">
      <h1>AI Smart Translator</h1>
      
      {/* Controls Section */}
      <div style={{ marginBottom: '15px', display: 'flex', gap: '10px' }}>
        <select 
          value={targetLang} 
          onChange={(e) => setTargetLang(e.target.value)}
          style={{ padding: '10px', borderRadius: '5px' }}
        >
          <option value="English">Translate to English</option>
          <option value="Bengali">Translate to Bangla</option>
          <option value="French">Translate to French</option>
          <option value="Spanish">Translate to Spanish</option>
          <option value="German">Translate to German</option>
        </select>
        
        <button onClick={handleTranslate} disabled={loading || !inputText.trim()}>
          {loading ? "Translating..." : "Go"}
        </button>
      </div>

      {/* Input Section - Auto detects direction */}
      <div className="input-area">
        <textarea 
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Type here (Example: مرحبًا كيف حالك)..."
          dir={isRTL ? "rtl" : "ltr"} // Auto-flips text direction while typing
          style={{ textAlign: isRTL ? 'right' : 'left' }}
        />
      </div>

      {/* ERROR MESSAGE */}
      {error && (
        <div style={{color: 'red', margin: '20px 0', padding: '10px', border: '1px solid red'}}>
          <h3>Error:</h3>
          <p>{error}</p>
        </div>
      )}

      {/* RESULTS */}
      {data && data.word_mapping ? (
        <div style={{ marginTop: '20px' }}>
          <h3>Translation ({targetLang}):</h3>
          {/* The translation result is usually LTR (like English) */}
          <p style={{ fontSize: '1.2rem', padding: '10px', background: '#f0f0f0', borderRadius: '5px' }}>
            {data.full_translation}
          </p>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px' }}>
            <h3>Interactive Reader (Source):</h3>
            <button 
              onClick={() => setShowAllMode(!showAllMode)} 
              style={{ background: '#28a745', fontSize: '0.8rem' }}
            >
              {showAllMode ? "Hide Meanings" : "Show All Meanings"}
            </button>
          </div>

          {/* This box flips to RTL if the source was Arabic */}
          <div 
            className={`result-box ${showAllMode ? 'show-all' : ''} ${isRTL ? 'rtl-mode' : ''}`}
          >
            {data.word_mapping.map((item, index) => (
              <span 
                key={index} 
                className="interactive-word" 
                data-trans={item.translated}
              >
                {item.original}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default App;
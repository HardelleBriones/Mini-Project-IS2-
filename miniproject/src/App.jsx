import React, { useState } from 'react';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [expandedIndex, setExpandedIndex] = useState(null);

  const handleInputChange = (event) => {
    setQuery(event.target.value);
  };

  const handleSearch = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const handleExpand = (index) => {
    setExpandedIndex(index === expandedIndex ? null : index);
  };

  return (
    <div className="container">
      <h1 className="title">Search App</h1>
      <input className="input" type="text" value={query} onChange={handleInputChange} />
      <button className="button" onClick={handleSearch}>Search</button>

      <div className="results">
        <h2 className="results-title">Results:</h2>
        <ul>
          {results.map((result, index) => (
            <li key={index} className="result-item">
              <h3 className="result-title" onClick={() => handleExpand(index)}>
                {result.question_title}
              </h3>
              {expandedIndex === index && (
                <div className="result-details">
                  <p className="result-body">{result.question_body}</p>
                  <p className="result-body">{result.question_answer}</p>
                </div>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App;

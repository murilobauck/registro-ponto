import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Portaria from './pages/Portaria/Portaria';
import Rh from './pages/Rh/Rh';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Portaria />} />
      <Route path="/rh" element={<Rh />} />
    </Routes>
  );
}

export default App;

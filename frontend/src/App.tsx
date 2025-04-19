import { useState } from 'react';
import ResumeUploader from './components/ResumeUploader';

function App() {
  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <ResumeUploader />
    </div>
  );
}

export default App;
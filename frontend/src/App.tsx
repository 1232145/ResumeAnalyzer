import { useState } from 'react';
import ResumeUploader from './components/ResumeUploader';
import JobDescriptionInput from './components/JobDescriptionInput';
import ResultsDisplay from './components/ResultsDisplay';
import { AnalysisResult, ComparisonResult } from './types/types';

function App() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1>Resume Analyzer</h1>

      <ResumeUploader onAnalysisComplete={setAnalysisResult} />

      {analysisResult && (
        <>
          <JobDescriptionInput
            resumeKeywords={analysisResult.keywords}
            onComparisonComplete={setComparisonResult}
          />
          <ResultsDisplay result={comparisonResult} />
        </>
      )}
    </div>
  );
}

export default App;
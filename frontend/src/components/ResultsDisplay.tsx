import { ComparisonResult } from '../types/types';

const ResultsDisplay = ({ result }: { result: ComparisonResult | null }) => {
    if (!result) return null;

    return (
        <div>
            <h3>✅ Matching Keywords:</h3>
            <ul>
                {result.matches.map((word) => (
                    <li key={word}>{word}</li>
                ))}
            </ul>

            <h3>❌ Missing Keywords:</h3>
            <ul>
                {result.missing.map((word) => (
                    <li key={word}>{word}</li>
                ))}
            </ul>
        </div>
    );
};

export default ResultsDisplay;
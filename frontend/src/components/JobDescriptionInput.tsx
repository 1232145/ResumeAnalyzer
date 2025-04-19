import { useState } from 'react';
import axios from 'axios';
import { ComparisonResult } from '../types/types';

const JobDescriptionInput = ({ resumeKeywords, onComparisonComplete }: {
    resumeKeywords: string[];
    onComparisonComplete: (result: ComparisonResult) => void;
}) => {
    const [jobDesc, setJobDesc] = useState('');

    const handleCompare = async () => {
        if (!jobDesc.trim()) return;

        try {
            const response = await axios.post('http://localhost:5000/compare', {
                resume_keywords: resumeKeywords,
                job_description: jobDesc,
            });
            onComparisonComplete(response.data);
        } catch (error) {
            console.error('Error comparing keywords:', error);
        }
    };

    return (
        <div>
            <textarea
                value={jobDesc}
                onChange={(e) => setJobDesc(e.target.value)}
                placeholder="Paste job description here"
                rows={5}
                style={{ width: '100%' }}
            />
            <button onClick={handleCompare} disabled={!jobDesc.trim()}>
                Compare with Resume
            </button>
        </div>
    );
};

export default JobDescriptionInput;
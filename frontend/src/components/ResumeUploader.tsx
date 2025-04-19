import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { AnalysisResult } from '../types/types';
import api from '../api';

const ResumeAnalyzer = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [extractedText, setExtractedText] = useState('');
    const [keywords, setKeywords] = useState<string[]>([]);
    const [resumeUrl, setResumeUrl] = useState('');
    const [comparison, setComparison] = useState<{
        matches: string[];
        missing: string[];
    } | null>(null);
    const [jobDesc, setJobDesc] = useState('');
    const [isTextExpanded, setIsTextExpanded] = useState(false);

    // File upload handler
    const onDrop = useCallback(async (files: File[]) => {
        const file = files[0];
        if (!file) return;

        setIsLoading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await api.post<AnalysisResult>(
                '/parse-resume',
                formData,
                { headers: { 'Content-Type': 'multipart/form-data' } }
            );

            setExtractedText(response.data.text);
            setKeywords(response.data.keywords);
            if (response.data.resume_url) setResumeUrl(response.data.resume_url);
        } catch (error) {
            console.error('Upload error:', error);
            alert('Upload failed. Check console for details.');
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Job description comparison
    const handleCompare = async () => {
        if (!jobDesc.trim() || keywords.length === 0) return;

        try {
            const response = await api.post('/compare', {
                resume_keywords: keywords,
                job_description: jobDesc
            });
            setComparison(response.data);
        } catch (error) {
            console.error('Comparison error:', error);
        }
    };

    const { getRootProps, getInputProps } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
        },
        maxFiles: 1,
        disabled: isLoading
    });

    return (
        <div className="container" style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
            <h1>Resume Analyzer</h1>

            {/* File Upload */}
            <div
                {...getRootProps()}
                style={dropzoneStyle(isLoading)}
            >
                <input {...getInputProps()} />
                {isLoading ? (
                    <p>Processing...</p>
                ) : (
                    <p>Drag & drop resume (PDF/DOCX), or click to select</p>
                )}
            </div>

            {/* Extracted Text */}

            {extractedText && (
                <div style={sectionStyle}>
                    <h3>📄 Extracted Text</h3>
                    <div style={textBoxStyle}>
                        {isTextExpanded
                            ? extractedText
                            : `${extractedText.substring(0, 500)}...`}
                    </div>
                    <button
                        onClick={() => setIsTextExpanded(!isTextExpanded)}
                        style={{...toggleButtonStyle, marginRight: '10px'}}
                    >
                        {isTextExpanded ? 'Show Less' : 'Show More'}
                    </button>
                    {resumeUrl && (
                        <a href={resumeUrl} target="_blank" rel="noopener noreferrer" style={linkStyle}>
                            View Full Resume
                        </a>
                    )}
                </div>
            )}

            {/* Keywords */}
            {keywords.length > 0 && (
                <div style={sectionStyle}>
                    <KeywordsSection
                        keywords={keywords}
                        onCompare={handleCompare}
                        jobDesc={jobDesc}
                        setJobDesc={setJobDesc}
                    />
                </div>
            )}

            {/* Comparison Results */}
            {comparison && (
                <div style={sectionStyle}>
                    <h3>🔍 Comparison Results</h3>
                    <div style={{ display: 'flex', gap: '20px' }}>
                        <KeywordList title="✅ Matches" keywords={comparison.matches} color="#e6f7e6" />
                        <KeywordList title="❌ Missing" keywords={comparison.missing} color="#ffe6e6" />
                    </div>
                </div>
            )}
        </div>
    );
};

// Sub-components
const KeywordsSection = ({
    keywords,
    jobDesc,
    setJobDesc,
    onCompare,
}: {
    keywords: string[];
    jobDesc: string;
    setJobDesc: (text: string) => void;
    onCompare: () => void;
}) => {
    const [showKeywords, setShowKeywords] = useState(false);

    return (
        <>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h3>🔑 Keywords ({keywords.length})</h3>
                <button
                    onClick={() => setShowKeywords(!showKeywords)}
                    style={toggleButtonStyle}
                >
                    {showKeywords ? 'Hide' : 'Show'}
                </button>
            </div>

            {showKeywords && (
                <div style={keywordsContainerStyle}>
                    {keywords.map((word, index) => (
                        <span key={index} style={keywordStyle}>
                            {word}
                        </span>
                    ))}
                </div>
            )}

            <div style={{ marginTop: '20px' }}>
                <h4>Compare with Job Description</h4>
                <textarea
                    value={jobDesc}
                    onChange={(e) => setJobDesc(e.target.value)}
                    placeholder="Paste job description here..."
                    style={textAreaStyle}
                />
                <button
                    onClick={onCompare}
                    disabled={!jobDesc.trim()}
                    style={compareButtonStyle(!jobDesc.trim())}
                >
                    Compare
                </button>
            </div>
        </>
    );
};

const KeywordList = ({ title, keywords, color }: { title: string; keywords: string[]; color: string }) => (
    <div style={{ flex: 1 }}>
        <h4>{title}</h4>
        <div style={{ ...keywordsContainerStyle, background: color }}>
            {keywords.length > 0 ? (
                keywords.map((word, index) => (
                    <span key={index} style={keywordStyle}>
                        {word}
                    </span>
                ))
            ) : (
                <p>None</p>
            )}
        </div>
    </div>
);

// Styles
const dropzoneStyle = (isLoading: boolean) => ({
    border: '2px dashed #aaa',
    borderRadius: '5px',
    padding: '30px',
    textAlign: 'center' as const,
    cursor: isLoading ? 'wait' : 'pointer',
    background: isLoading ? '#f5f5f5' : 'white',
    marginBottom: '20px'
});

const sectionStyle = {
    background: '#f9f9f9',
    padding: '20px',
    borderRadius: '5px',
    marginBottom: '20px'
};

const textBoxStyle = {
    maxHeight: '300px',
    overflowY: 'auto' as const,
    background: 'white',
    padding: '15px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    margin: '10px 0',
    whiteSpace: 'pre-wrap' as const
};

const keywordsContainerStyle = {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '8px',
    margin: '10px 0',
    padding: '10px',
    borderRadius: '4px'
};

const keywordStyle = {
    background: '#e0f7fa',
    padding: '3px 10px',
    borderRadius: '20px',
    fontSize: '14px'
};

const linkStyle = {
    color: '#0066cc',
    textDecoration: 'none',
    display: 'inline-block',
    marginTop: '10px'
};

const toggleButtonStyle = {
    background: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '20px',
    padding: '8px 16px',
    fontSize: '14px',
    cursor: 'pointer',
    transition: 'background-color 0.3s ease',
    display: 'inline-block',
};

const textAreaStyle = {
    width: '100%',
    minHeight: '100px',
    padding: '10px',
    margin: '10px 0',
    borderRadius: '4px',
    border: '1px solid #ddd'
};

const compareButtonStyle = (disabled: boolean) => ({
    background: disabled ? '#ccc' : '#4CAF50',
    color: 'white',
    border: 'none',
    padding: '8px 16px',
    borderRadius: '4px',
    cursor: disabled ? 'not-allowed' : 'pointer'
});

export default ResumeAnalyzer;
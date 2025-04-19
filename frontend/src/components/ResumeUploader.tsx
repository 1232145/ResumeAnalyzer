import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { AnalysisResult } from '../types/types';
import api from '../api';

const ResumeUploader = ({ onAnalysisComplete }: { onAnalysisComplete: (result: AnalysisResult) => void }) => {
    const [isLoading, setIsLoading] = useState(false);
    const [extractedText, setExtractedText] = useState('');
    const [keywords, setKeywords] = useState<string[]>([]);
    const [showKeywords, setShowKeywords] = useState(false);

    const onDrop = useCallback(async (files: File[]) => {
        const file = files[0];
        if (!file) return;

        setIsLoading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await api.post(
                '/parse-resume',
                formData,
                { headers: { 'Content-Type': 'multipart/form-data' } }
            );

            // Update state with extracted data
            setExtractedText(response.data.text || 'No text extracted');
            setKeywords(response.data.keywords || []);
            onAnalysisComplete(response.data);

        } catch (error) {
            console.error('Error uploading file:', error);
        } finally {
            setIsLoading(false);
        }
    }, [onAnalysisComplete]);

    const { getRootProps, getInputProps } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
        },
        maxFiles: 1,
    });

    return (
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            {/* File Upload Zone */}
            <div
                {...getRootProps()}
                style={{
                    border: '2px dashed #ccc',
                    padding: '20px',
                    textAlign: 'center',
                    marginBottom: '20px',
                    cursor: 'pointer'
                }}
            >
                <input {...getInputProps()} />
                {isLoading ? (
                    <p>Processing resume...</p>
                ) : (
                    <p>Drag & drop a resume (PDF/DOCX), or click to select</p>
                )}
            </div>

            {/* Extracted Content Display */}
            {extractedText && (
                <div style={{
                    background: '#f5f5f5',
                    padding: '15px',
                    borderRadius: '8px',
                    marginBottom: '20px'
                }}>
                    <h3>📄 Extracted Text:</h3>
                    <div style={{
                        maxHeight: '200px',
                        overflowY: 'auto',
                        whiteSpace: 'pre-wrap',
                        fontFamily: 'monospace',
                        background: 'white',
                        padding: '10px',
                        border: '1px solid #ddd'
                    }}>
                        {extractedText}
                    </div>
                </div>
            )}

            {/* Keywords Display */}
            {keywords.length > 0 && (
                <div style={{ margin: '20px 0' }}>
                    <button
                        onClick={() => setShowKeywords(!showKeywords)}
                        style={{
                            background: 'none',
                            border: 'none',
                            color: '#0066cc',
                            cursor: 'pointer',
                            padding: '5px 0'
                        }}
                    >
                        {showKeywords ? '▼' : '▶'} Identified Keywords ({keywords.length})
                    </button>

                    {showKeywords && (
                        <div style={{
                            maxHeight: '150px',
                            overflowY: 'auto',
                            marginTop: '10px',
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: '8px'
                        }}>
                            {keywords.map((word) => (
                                <span
                                    key={word}
                                    style={{
                                        background: '#e0f7fa',
                                        padding: '3px 8px',
                                        borderRadius: '12px',
                                        fontSize: '13px'
                                    }}
                                >
                                    {word}
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ResumeUploader;
export type AnalysisResult = {
    text: string;
    keywords: string[];
    resume_url?: string;
  };
  
  export type ComparisonResult = {
    matches: string[];
    missing: string[];
  };
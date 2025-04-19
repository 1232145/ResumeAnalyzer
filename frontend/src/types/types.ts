export type AnalysisResult = {
    text: string;
    keywords: string[];
  };
  
  export type ComparisonResult = {
    matches: string[];
    missing: string[];
  };
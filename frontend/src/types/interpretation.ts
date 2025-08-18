export interface Interpretation {
  _id?: string;
  testName: string;
  testType: string;
  isActive: boolean;
  results: InterpretationResults;
  createdAt?: string;
  updatedAt?: string;
}

export interface InterpretationResults {
  dimensions: Record<string, any>;
  topN?: number;
  overview?: string;
}

// Personal Values specific types
export interface PersonalValuesDimension {
  title: string;
  description: string;
  manifestation: string;
  strengthChallenges: string;
}

export interface PersonalValuesResults extends InterpretationResults {
  dimensions: {
    achievement?: PersonalValuesDimension;
    benevolence?: PersonalValuesDimension;
    conformity?: PersonalValuesDimension;
    hedonism?: PersonalValuesDimension;
    power?: PersonalValuesDimension;
    security?: PersonalValuesDimension;
    selfDirection?: PersonalValuesDimension;
    stimulation?: PersonalValuesDimension;
    tradition?: PersonalValuesDimension;
    universalism?: PersonalValuesDimension;
  };
  topN: number;
}

// Personality specific types
export interface PersonalityDimensionLevel {
  interpretation: string;
  overview: string;
  aspekKehidupan: {
    gayaBelajar: string[];
    hubunganInterpersonal: string[];
    karir: string[];
    kekuatan: string[];
    kelemahan: string[];
    kepemimpinan: string[];
  };
  rekomendasi: {
    title: string;
    description: string;
  }[];
}

export interface PersonalityDimension {
  rendah?: PersonalityDimensionLevel;
  sedang?: PersonalityDimensionLevel;
  tinggi?: PersonalityDimensionLevel;
}

export interface PersonalityResults extends InterpretationResults {
  dimensions: {
    agreeableness?: PersonalityDimension;
    conscientiousness?: PersonalityDimension;
    extraversion?: PersonalityDimension;
    neuroticism?: PersonalityDimension;
    openness?: PersonalityDimension;
  };
  overview: string;
}

// Legacy types for backward compatibility
export interface InterpretationDimension {
  name: string;
  ranges: InterpretationRange[];
}

export interface InterpretationRange {
  min: number;
  max: number;
  aspekKehidupan: string;
  rekomendasi: string;
}

export interface CreateInterpretationRequest {
  testName: string;
  testType: string;
  results: InterpretationResults;
}

export interface UpdateInterpretationRequest {
  testName?: string;
  testType?: string;
  isActive?: boolean;
  results?: InterpretationResults;
}

export interface InterpretationListResponse {
  interpretations: Interpretation[];
  total: number;
  success: boolean;
}

export interface InterpretationResponse {
  interpretation: Interpretation;
}
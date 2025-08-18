import React, { useState } from 'react';
import { Interpretation, PersonalValuesResults, PersonalityResults } from '../types/interpretation';
import JsonViewer from './JsonViewer';
import { interpretationService } from '../services/interpretationService';
import { Eye, EyeOff, Power, PowerOff } from 'lucide-react';

interface InterpretationDisplayProps {
  interpretation: Interpretation;
  className?: string;
  onUpdate?: (updatedInterpretation: Interpretation) => void;
}

const InterpretationDisplay: React.FC<InterpretationDisplayProps> = ({ 
  interpretation, 
  className = '',
  onUpdate
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<'json' | 'formatted'>('json');
  const [isUpdating, setIsUpdating] = useState(false);

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const handleIsActiveToggle = async () => {
    if (isUpdating || !interpretation._id) return;
    
    setIsUpdating(true);
    try {
      const updatedInterpretation = await interpretationService.update(
        interpretation._id,
        { isActive: !interpretation.isActive }
      );
      if (onUpdate) {
        onUpdate(updatedInterpretation);
      }
    } catch (error) {
      console.error('Failed to update interpretation:', error);
    } finally {
      setIsUpdating(false);
    }
  };

  const renderPersonalValues = (results: PersonalValuesResults) => {
    const dimensions = results.dimensions || {};
    const dimensionKeys = Object.keys(dimensions);

    return (
      <div className="personal-values-display">
        {results.overview && (
          <div className="overview-section">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">Overview</h3>
            <p className="text-gray-600 leading-relaxed">{results.overview}</p>
          </div>
        )}
        
        <div className="dimensions-grid">
          {dimensionKeys.map((key, index) => {
            const dimension = dimensions[key as keyof typeof dimensions];
            const isExpanded = expandedSections.has(key);
            
            if (!dimension) return null;
            
            return (
              <div key={key} className="dimension-card">
                <div 
                  className="dimension-header"
                  onClick={() => toggleSection(key)}
                >
                  <div className="dimension-title">
                    <span className="dimension-number">#{index + 1}</span>
                    <h4 className="text-xl font-bold text-gray-900">
                      {dimension.title}
                    </h4>
                  </div>
                  <div className="dimension-subtitle text-gray-600">
                    {dimension.description}
                  </div>
                  <button className="expand-button">
                    {isExpanded ? '−' : '+'}
                  </button>
                </div>
                
                {isExpanded && (
                  <div className="dimension-content">
                    <div className="content-section">
                      <h5 className="section-title">Description</h5>
                      <p className="section-text">{dimension.description}</p>
                    </div>
                    
                    <div className="content-section">
                      <h5 className="section-title">Manifestation</h5>
                      <p className="section-text">{dimension.manifestation}</p>
                    </div>
                    
                    <div className="content-section">
                      <h5 className="section-title">Strengths & Challenges</h5>
                      <p className="section-text">{dimension.strengthChallenges}</p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderPersonality = (results: PersonalityResults) => {
    const dimensions = results.dimensions || {};
    const dimensionKeys = Object.keys(dimensions);

    return (
      <div className="personality-display">
        {results.overview && (
          <div className="overview-section">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">Overview</h3>
            <p className="text-gray-600 leading-relaxed">{results.overview}</p>
          </div>
        )}
        
        <div className="dimensions-grid">
          {dimensionKeys.map((key) => {
            const dimension = dimensions[key as keyof typeof dimensions];
            const isExpanded = expandedSections.has(key);
            
            if (!dimension) return null;
            
            return (
              <div key={key} className="dimension-card">
                <div 
                  className="dimension-header"
                  onClick={() => toggleSection(key)}
                >
                  <div className="dimension-title">
                    <h4 className="text-xl font-bold text-gray-900 capitalize">
                      {key.replace(/([A-Z])/g, ' $1').trim()}
                    </h4>
                  </div>
                  <button className="expand-button">
                    {isExpanded ? '−' : '+'}
                  </button>
                </div>
                
                {isExpanded && (
                  <div className="dimension-content">
                    {Object.entries(dimension).map(([level, levelData]) => {
                      const typedLevelData = levelData as any;
                      return (
                        <div key={level} className="level-section">
                          <h5 className="level-title capitalize">{level}</h5>
                          <div className="level-content">
                            <div className="interpretation-section">
                              <h6 className="subsection-title">Interpretation</h6>
                              <p className="subsection-text">{typedLevelData.interpretation}</p>
                            </div>
                            
                            <div className="overview-section">
                              <h6 className="subsection-title">Overview</h6>
                              <p className="subsection-text">{typedLevelData.overview}</p>
                            </div>
                            
                            {typedLevelData.aspekKehidupan && (
                              <div className="aspects-section">
                                <h6 className="subsection-title">Life Aspects</h6>
                                <div className="aspects-grid">
                                  {Object.entries(typedLevelData.aspekKehidupan).map(([aspect, items]: [string, any]) => (
                                    <div key={aspect} className="aspect-group">
                                      <h6 className="aspect-title capitalize">
                                        {aspect.replace(/([A-Z])/g, ' $1').trim()}
                                      </h6>
                                      <ul className="aspect-list">
                                        {Array.isArray(items) && items.map((item: string, index: number) => (
                                          <li key={index} className="aspect-item">{item}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {typedLevelData.rekomendasi && (
                              <div className="recommendations-section">
                                <h6 className="subsection-title">Recommendations</h6>
                                <div className="recommendations-list">
                                  {typedLevelData.rekomendasi.map((rec: any, index: number) => (
                                    <div key={index} className="recommendation-item">
                                      <h6 className="recommendation-title">{rec.title}</h6>
                                      <p className="recommendation-text">{rec.description}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderCustomFormat = (results: any) => {
    // For custom formats, render as a structured display
    return (
      <div className="custom-format-display">
        <div className="json-tree">
          {Object.entries(results).map(([key, value]) => (
            <div key={key} className="tree-node">
              <div 
                className="tree-header"
                onClick={() => toggleSection(key)}
              >
                <span className="tree-key">{key}</span>
                <button className="expand-button">
                  {expandedSections.has(key) ? '−' : '+'}
                </button>
              </div>
              
              {expandedSections.has(key) && (
                <div className="tree-content">
                  {typeof value === 'object' && value !== null ? (
                    <pre className="json-content">
                      {JSON.stringify(value, null, 2)}
                    </pre>
                  ) : (
                    <span className="tree-value">{String(value)}</span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderContent = () => {
    const { results, testType } = interpretation;

    switch (testType) {
      case 'top-n-dimension':
        return renderPersonalValues(results as PersonalValuesResults);
      case 'multiple-dimension':
        return renderPersonality(results as PersonalityResults);
      default:
        return renderCustomFormat(results);
    }
  };

  return (
    <div className={`interpretation-display ${className}`}>
      <div className="interpretation-header">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {interpretation.testName}
            </h2>
            <div className="interpretation-meta">
              <span className="test-type-badge">
                {interpretation.testType}
              </span>
              {interpretation.createdAt && (
                <span className="created-date">
                  Created: {new Date(interpretation.createdAt).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* isActive Toggle */}
            <button
              onClick={handleIsActiveToggle}
              disabled={isUpdating}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors cursor-pointer ${
                interpretation.isActive
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-400 text-white hover:bg-gray-500'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
              title={interpretation.isActive ? 'Active' : 'Inactive'}
            >
              {interpretation.isActive ? <Power size={16} /> : <PowerOff size={16} />}
              {isUpdating ? 'Updating...' : (interpretation.isActive ? 'Active' : 'Inactive')}
            </button>
            
            {/* View Mode Toggle */}
            <button
              onClick={() => setViewMode(viewMode === 'json' ? 'formatted' : 'json')}
              className="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors cursor-pointer"
              title={viewMode === 'json' ? 'Switch to Formatted View' : 'Switch to JSON View'}
            >
              {viewMode === 'json' ? <EyeOff size={16} /> : <Eye size={16} />}
              {viewMode === 'json' ? 'Show Formatted' : 'Show JSON'}
            </button>
          </div>
        </div>
      </div>
      
      <div className="interpretation-content">
        {viewMode === 'formatted' ? renderContent() : (
          <JsonViewer 
            data={interpretation.results} 
            defaultExpandDepth={2}
            searchable={true}
            editable={false}
            className="mt-4"
          />
        )}
      </div>
      
      <style>{`
        .interpretation-display {
          background-color: white;
          border-radius: 0.75rem;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
          overflow: hidden;
        }
        
        .interpretation-header {
          background: linear-gradient(to right, rgb(248, 250, 252), rgb(243, 244, 246));
          backdrop-filter: blur(8px);
          border-bottom: 1px solid #e5e7eb;
          padding: 1.5rem;
        }
        
        .interpretation-content {
          padding: 1.5rem;
        }
        
        .interpretation-meta {
          display: flex;
          align-items: center;
          gap: 1rem;
          font-size: 0.875rem;
          color: #6b7280;
        }
        
        .test-type-badge {
          background-color: #dbeafe;
          color: #1e40af;
          padding: 0.25rem 0.5rem;
          border-radius: 9999px;
          font-size: 0.75rem;
          font-weight: 500;
        }
        
        .created-date {
          color: #6b7280;
        }
        
        .overview-section {
          margin-bottom: 1.5rem;
          padding: 1rem;
          background-color: #f9fafb;
          border-radius: 0.5rem;
        }
        
        .dimensions-grid {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        
        .dimension-card {
          border: 1px solid #e5e7eb;
          border-radius: 0.5rem;
          overflow: hidden;
        }
        
        .dimension-header {
          background: linear-gradient(to right, #eff6ff, #eef2ff);
          padding: 1rem;
          cursor: pointer;
          transition: background-color 0.2s;
        }
        
        .dimension-header:hover {
          background: linear-gradient(to right, #dbeafe, #e0e7ff);
        }
        
        .dimension-title {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        
        .dimension-number {
          background-color: #3b82f6;
          color: white;
          width: 2rem;
          height: 2rem;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.875rem;
          font-weight: bold;
        }
        
        .dimension-subtitle {
          margin-top: 0.5rem;
          font-size: 0.875rem;
          font-style: italic;
          color: #6b7280;
        }
        
        .expand-button {
          margin-left: auto;
          background-color: white;
          border: 1px solid #d1d5db;
          width: 1.5rem;
          height: 1.5rem;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #4b5563;
          transition: background-color 0.2s;
        }
        
        .expand-button:hover {
          background-color: #f9fafb;
        }
        
        .dimension-content {
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        
        .content-section {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        
        .section-title {
          font-size: 0.875rem;
          font-weight: 600;
          color: #374151;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        
        .section-text {
          color: #4b5563;
          line-height: 1.625;
        }
        
        .level-section {
          border-left: 4px solid #bfdbfe;
          padding-left: 1rem;
          margin-bottom: 1rem;
        }
        
        .level-title {
          font-size: 1.125rem;
          font-weight: 600;
          color: #1f2937;
          margin-bottom: 0.75rem;
        }
        
        .level-content {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        
        .subsection-title {
          font-size: 0.875rem;
          font-weight: 600;
          color: #374151;
          margin-bottom: 0.5rem;
        }
        
        .subsection-text {
          color: #4b5563;
          line-height: 1.625;
        }
        
        .aspects-grid {
          display: grid;
          grid-template-columns: repeat(1, 1fr);
          gap: 1rem;
        }
        
        @media (min-width: 768px) {
          .aspects-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }
        
        .aspect-group {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        
        .aspect-title {
          font-size: 0.875rem;
          font-weight: 500;
          color: #374151;
        }
        
        .aspect-list {
          list-style-type: disc;
          list-style-position: inside;
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }
        
        .aspect-item {
          font-size: 0.875rem;
          color: #4b5563;
        }
        
        .recommendations-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }
        
        .recommendation-item {
          padding: 0.75rem;
          background-color: #fef3c7;
          border-left: 4px solid #fbbf24;
          border-radius: 0.25rem;
        }
        
        .recommendation-title {
          font-size: 0.875rem;
          font-weight: 600;
          color: #92400e;
          margin-bottom: 0.25rem;
          display: block;
        }
        
        .recommendation-text {
          font-size: 0.875rem;
          color: #a16207;
        }
        
        .custom-format-display {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        
        .json-tree {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }
        
        .tree-node {
          border: 1px solid #e5e7eb;
          border-radius: 0.25rem;
        }
        
        .tree-header {
          background-color: #f9fafb;
          padding: 0.75rem;
          cursor: pointer;
          transition: background-color 0.2s;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        
        .tree-header:hover {
          background-color: #f3f4f6;
        }
        
        .tree-key {
          font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
          font-size: 0.875rem;
          font-weight: 500;
          color: #374151;
        }
        
        .tree-content {
          padding: 0.75rem;
          background-color: white;
        }
        
        .json-content {
          font-size: 0.875rem;
          color: #4b5563;
          font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
          white-space: pre-wrap;
        }
        
        .tree-value {
          font-size: 0.875rem;
          color: #4b5563;
        }
      `}</style>
    </div>
  );
};

export default InterpretationDisplay;

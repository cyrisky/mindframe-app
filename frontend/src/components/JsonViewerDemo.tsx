import React from 'react';
import JsonViewer from './JsonViewer';

const sampleData = {
  personalValues: {
    title: "Personal Values Assessment",
    description: "A comprehensive analysis of your core personal values and their manifestations in daily life.",
    dimensions: {
      achievement: {
        score: 85,
        level: "High",
        description: "You strongly value setting and accomplishing meaningful goals. You find satisfaction in completing tasks and seeing tangible results from your efforts.",
        manifestation: "You often set ambitious goals and work systematically to achieve them. You track your progress and celebrate milestones along the way.",
        areas: ["Career advancement", "Skill development", "Project completion"],
        examples: [
          "Completing a major project ahead of schedule",
          "Learning a new skill and applying it successfully",
          "Receiving recognition for your accomplishments"
        ]
      },
      relationships: {
        score: 92,
        level: "Very High",
        description: "You place great importance on building and maintaining meaningful connections with others. You value trust, empathy, and mutual support in your relationships.",
        manifestation: "You invest time and energy in nurturing relationships. You're often the person others turn to for support and advice.",
        areas: ["Family bonds", "Friendships", "Professional networks"],
        examples: [
          "Regularly checking in with friends and family",
          "Being a supportive colleague and mentor",
          "Building trust through consistent, reliable behavior"
        ]
      },
      creativity: {
        score: 78,
        level: "Moderate-High",
        description: "You appreciate innovation and original thinking. You enjoy exploring new ideas and finding unique solutions to problems.",
        manifestation: "You often approach challenges from different angles and enjoy brainstorming sessions. You appreciate art, music, and creative expression.",
        areas: ["Problem-solving", "Artistic expression", "Innovation"],
        examples: [
          "Coming up with creative solutions to work challenges",
          "Enjoying creative hobbies like painting or writing",
          "Encouraging innovative thinking in team settings"
        ]
      }
    },
    summary: {
      topValues: ["relationships", "achievement", "creativity"],
      overallScore: 85,
      recommendations: [
        "Focus on building deeper connections in your professional network",
        "Set specific, measurable goals that align with your values",
        "Explore creative outlets that can enhance your problem-solving skills"
      ]
    }
  },
  metadata: {
    assessmentDate: "2024-01-15",
    version: "2.1.0",
    duration: "15 minutes",
    questions: 45,
    confidence: 0.89
  }
};

const JsonViewerDemo: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          Improved JSON Viewer Demo
        </h1>
        <p className="text-muted-foreground">
          Showcasing the enhanced JsonViewer component with shadcn/ui components
        </p>
      </div>

      <div className="grid gap-6">
        <JsonViewer
          data={sampleData}
          title="Personal Values Assessment Data"
          description="Interactive exploration of personal values assessment results with search and navigation capabilities"
          searchable={true}
          editable={false}
          defaultExpandDepth={2}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <JsonViewer
            data={sampleData.personalValues.dimensions}
            title="Dimensions Data"
            description="Detailed breakdown of personal value dimensions"
            searchable={true}
            editable={false}
            defaultExpandDepth={1}
          />

          <JsonViewer
            data={sampleData.metadata}
            title="Metadata"
            description="Assessment metadata and configuration"
            searchable={true}
            editable={false}
            defaultExpandDepth={1}
          />
        </div>
      </div>
    </div>
  );
};

export default JsonViewerDemo;

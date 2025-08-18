import pytest
import weasyprint
import json
from datetime import datetime
from typing import Dict, Any


class TestMindframePDFExamples:
    """Test WeasyPrint with realistic Mindframe app scenarios."""
    
    def test_anxiety_assessment_report(self):
        """Test PDF generation for anxiety assessment report."""
        # Sample assessment data
        assessment_data = {
            'user_name': 'John Doe',
            'assessment_type': 'Anxiety Assessment',
            'date': '2024-01-15',
            'scores': {
                'gad7_score': 8,
                'gad7_severity': 'Mild',
                'panic_score': 3,
                'social_anxiety_score': 12,
                'overall_anxiety_level': 'Moderate'
            },
            'recommendations': [
                'Practice deep breathing exercises daily',
                'Consider cognitive behavioral therapy',
                'Maintain regular sleep schedule',
                'Limit caffeine intake'
            ]
        }
        
        html_content = self._generate_anxiety_report_html(assessment_data)
        
        # Generate PDF
        html_doc = weasyprint.HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        # Save to file for inspection
        with open('mindframe_anxiety_report.pdf', 'wb') as f:
            f.write(pdf_bytes)
        print('✓ Mindframe Anxiety Assessment PDF created: mindframe_anxiety_report.pdf')
        
        # Verify PDF
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
        assert len(pdf_bytes) > 8000  # Substantial report
    
    def test_depression_screening_report(self):
        """Test PDF generation for depression screening report."""
        assessment_data = {
            'user_name': 'Jane Smith',
            'assessment_type': 'Depression Screening (PHQ-9)',
            'date': '2024-01-15',
            'scores': {
                'phq9_score': 12,
                'phq9_severity': 'Moderate',
                'risk_factors': ['Sleep disturbance', 'Low energy', 'Concentration issues'],
                'protective_factors': ['Strong social support', 'Regular exercise']
            },
            'recommendations': [
                'Schedule appointment with mental health professional',
                'Continue regular exercise routine',
                'Practice mindfulness meditation',
                'Monitor mood daily using app'
            ]
        }
        
        html_content = self._generate_depression_report_html(assessment_data)
        
        # Generate PDF
        html_doc = weasyprint.HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        # Save to file for inspection
        with open('mindframe_depression_report.pdf', 'wb') as f:
            f.write(pdf_bytes)
        print('✓ Mindframe Depression Screening PDF created: mindframe_depression_report.pdf')
        
        # Verify PDF
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
    
    def test_wellness_tracking_report(self):
        """Test PDF generation for wellness tracking summary."""
        tracking_data = {
            'user_name': 'Alex Johnson',
            'report_period': '30 days',
            'date_range': 'Dec 15, 2023 - Jan 15, 2024',
            'metrics': {
                'mood_average': 7.2,
                'stress_average': 4.1,
                'sleep_average': 7.8,
                'exercise_days': 22,
                'meditation_sessions': 18
            },
            'trends': {
                'mood': 'Improving',
                'stress': 'Stable',
                'sleep': 'Good',
                'exercise': 'Consistent'
            },
            'goals_achieved': 3,
            'total_goals': 5
        }
        
        html_content = self._generate_wellness_report_html(tracking_data)
        
        # Generate PDF
        html_doc = weasyprint.HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        # Save to file for inspection
        with open('mindframe_wellness_report.pdf', 'wb') as f:
            f.write(pdf_bytes)
        print('✓ Mindframe Wellness Tracking PDF created: mindframe_wellness_report.pdf')
        
        # Verify PDF
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
    
    def test_therapy_session_notes(self):
        """Test PDF generation for therapy session notes."""
        session_data = {
            'client_name': 'Sarah Wilson',
            'therapist_name': 'Dr. Emily Chen',
            'session_number': 8,
            'date': '2024-01-15',
            'duration': '50 minutes',
            'session_type': 'Individual Therapy',
            'presenting_concerns': [
                'Work-related stress',
                'Relationship difficulties',
                'Sleep issues'
            ],
            'interventions': [
                'Cognitive restructuring exercises',
                'Stress management techniques',
                'Communication skills practice'
            ],
            'homework': [
                'Practice thought challenging worksheet',
                'Implement sleep hygiene routine',
                'Use mindfulness app 10 min/day'
            ],
            'next_session': '2024-01-22'
        }
        
        html_content = self._generate_session_notes_html(session_data)
        
        # Generate PDF
        html_doc = weasyprint.HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        # Save to file for inspection
        with open('mindframe_session_notes.pdf', 'wb') as f:
            f.write(pdf_bytes)
        print('✓ Mindframe Therapy Session Notes PDF created: mindframe_session_notes.pdf')
        
        # Verify PDF
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
    
    def _generate_anxiety_report_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML for anxiety assessment report."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Anxiety Assessment Report</title>
            <meta charset="utf-8">
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                    @top-center {{
                        content: "Mindframe - Anxiety Assessment Report";
                        font-size: 10pt;
                        color: #666;
                    }}
                }}
                body {{
                    font-family: 'Helvetica', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .header {{
                    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                    color: white;
                    padding: 25px;
                    text-align: center;
                    border-radius: 8px;
                    margin-bottom: 30px;
                }}
                .section {{
                    margin-bottom: 25px;
                    padding: 20px;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    border-left: 4px solid #ff6b6b;
                }}
                .score-box {{
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 10px 0;
                    border: 1px solid #e9ecef;
                    display: inline-block;
                    min-width: 150px;
                    text-align: center;
                }}
                .score-value {{
                    font-size: 24pt;
                    font-weight: bold;
                    color: #ff6b6b;
                }}
                .severity-mild {{ color: #28a745; }}
                .severity-moderate {{ color: #ffc107; }}
                .severity-severe {{ color: #dc3545; }}
                ul {{ padding-left: 20px; }}
                li {{ margin-bottom: 8px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Anxiety Assessment Report</h1>
                <p>Patient: {data['user_name']}</p>
                <p>Date: {data['date']}</p>
            </div>
            
            <div class="section">
                <h2>Assessment Scores</h2>
                <div class="score-box">
                    <div>GAD-7 Score</div>
                    <div class="score-value">{data['scores']['gad7_score']}</div>
                    <div class="severity-mild">({data['scores']['gad7_severity']})</div>
                </div>
                <div class="score-box">
                    <div>Panic Score</div>
                    <div class="score-value">{data['scores']['panic_score']}</div>
                </div>
                <div class="score-box">
                    <div>Social Anxiety</div>
                    <div class="score-value">{data['scores']['social_anxiety_score']}</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Overall Assessment</h2>
                <p>Based on your responses, your overall anxiety level is classified as <strong>{data['scores']['overall_anxiety_level']}</strong>.</p>
                <p>This indicates that you may be experiencing some anxiety symptoms that could benefit from attention and management strategies.</p>
            </div>
            
            <div class="section">
                <h2>Recommendations</h2>
                <ul>
        """
        
        for rec in data['recommendations']:
            html_content += f"<li>{rec}</li>"
        
        html_content += """
                </ul>
            </div>
            
            <div class="section">
                <h2>Next Steps</h2>
                <p>We recommend implementing these strategies and tracking your progress using the Mindframe app. If symptoms persist or worsen, please consult with a mental health professional.</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_depression_report_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML for depression screening report."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Depression Screening Report</title>
            <meta charset="utf-8">
            <style>
                @page {{ size: A4; margin: 2cm; }}
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: #4a90e2; color: white; padding: 25px; text-align: center; border-radius: 8px; margin-bottom: 30px; }}
                .section {{ margin-bottom: 25px; padding: 20px; background-color: #f8f9fa; border-radius: 8px; }}
                .risk-factors {{ background: #fff3cd; border-left: 4px solid #ffc107; }}
                .protective-factors {{ background: #d4edda; border-left: 4px solid #28a745; }}
                .score {{ font-size: 20pt; font-weight: bold; color: #4a90e2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Depression Screening Report</h1>
                <p>Patient: {data['user_name']}</p>
                <p>Assessment: {data['assessment_type']}</p>
                <p>Date: {data['date']}</p>
            </div>
            
            <div class="section">
                <h2>PHQ-9 Results</h2>
                <p>Score: <span class="score">{data['scores']['phq9_score']}</span> ({data['scores']['phq9_severity']})</p>
                <p>This score suggests {data['scores']['phq9_severity'].lower()} depression symptoms.</p>
            </div>
            
            <div class="section risk-factors">
                <h2>Risk Factors Identified</h2>
                <ul>
        """
        
        for factor in data['scores']['risk_factors']:
            html_content += f"<li>{factor}</li>"
        
        html_content += """
                </ul>
            </div>
            
            <div class="section protective-factors">
                <h2>Protective Factors</h2>
                <ul>
        """
        
        for factor in data['scores']['protective_factors']:
            html_content += f"<li>{factor}</li>"
        
        html_content += """
                </ul>
            </div>
            
            <div class="section">
                <h2>Recommendations</h2>
                <ul>
        """
        
        for rec in data['recommendations']:
            html_content += f"<li>{rec}</li>"
        
        html_content += """
                </ul>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_wellness_report_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML for wellness tracking report."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Wellness Tracking Report</title>
            <meta charset="utf-8">
            <style>
                @page {{ size: A4; margin: 2cm; }}
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: #28a745; color: white; padding: 25px; text-align: center; border-radius: 8px; margin-bottom: 30px; }}
                .metrics-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
                .metric-card {{ background: white; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef; text-align: center; }}
                .metric-value {{ font-size: 18pt; font-weight: bold; color: #28a745; }}
                .section {{ margin-bottom: 25px; padding: 20px; background-color: #f8f9fa; border-radius: 8px; }}
                .progress-bar {{ background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden; }}
                .progress-fill {{ background: #28a745; height: 100%; transition: width 0.3s ease; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Wellness Tracking Report</h1>
                <p>User: {data['user_name']}</p>
                <p>Period: {data['report_period']} ({data['date_range']})</p>
            </div>
            
            <div class="section">
                <h2>Key Metrics</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div>Average Mood</div>
                        <div class="metric-value">{data['metrics']['mood_average']}/10</div>
                    </div>
                    <div class="metric-card">
                        <div>Average Stress</div>
                        <div class="metric-value">{data['metrics']['stress_average']}/10</div>
                    </div>
                    <div class="metric-card">
                        <div>Sleep Quality</div>
                        <div class="metric-value">{data['metrics']['sleep_average']}/10</div>
                    </div>
                    <div class="metric-card">
                        <div>Exercise Days</div>
                        <div class="metric-value">{data['metrics']['exercise_days']}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Goal Progress</h2>
                <p>Goals Achieved: {data['goals_achieved']} out of {data['total_goals']}</p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {(data['goals_achieved']/data['total_goals'])*100}%"></div>
                </div>
            </div>
            
            <div class="section">
                <h2>Trends Analysis</h2>
                <ul>
                    <li>Mood: {data['trends']['mood']}</li>
                    <li>Stress: {data['trends']['stress']}</li>
                    <li>Sleep: {data['trends']['sleep']}</li>
                    <li>Exercise: {data['trends']['exercise']}</li>
                </ul>
            </div>
        </body>
        </html>
        """
    
    def _generate_session_notes_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML for therapy session notes."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Therapy Session Notes</title>
            <meta charset="utf-8">
            <style>
                @page {{ size: A4; margin: 2cm; }}
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: #6c5ce7; color: white; padding: 25px; border-radius: 8px; margin-bottom: 30px; }}
                .session-info {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
                .info-box {{ background: #f8f9fa; padding: 15px; border-radius: 8px; }}
                .section {{ margin-bottom: 25px; padding: 20px; background-color: #f8f9fa; border-radius: 8px; }}
                .confidential {{ background: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="confidential">
                <strong>CONFIDENTIAL - THERAPY SESSION NOTES</strong>
            </div>
            
            <div class="header">
                <h1>Therapy Session Notes</h1>
                <div class="session-info">
                    <div class="info-box">
                        <strong>Client:</strong> {data['client_name']}<br>
                        <strong>Therapist:</strong> {data['therapist_name']}<br>
                        <strong>Session #:</strong> {data['session_number']}
                    </div>
                    <div class="info-box">
                        <strong>Date:</strong> {data['date']}<br>
                        <strong>Duration:</strong> {data['duration']}<br>
                        <strong>Type:</strong> {data['session_type']}
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Presenting Concerns</h2>
                <ul>
        """
        
        for concern in data['presenting_concerns']:
            html_content += f"<li>{concern}</li>"
        
        html_content += """
                </ul>
            </div>
            
            <div class="section">
                <h2>Interventions Used</h2>
                <ul>
        """
        
        for intervention in data['interventions']:
            html_content += f"<li>{intervention}</li>"
        
        html_content += """
                </ul>
            </div>
            
            <div class="section">
                <h2>Homework Assignments</h2>
                <ul>
        """
        
        for hw in data['homework']:
            html_content += f"<li>{hw}</li>"
        
        html_content += f"""
                </ul>
            </div>
            
            <div class="section">
                <h2>Next Session</h2>
                <p>Scheduled for: <strong>{data['next_session']}</strong></p>
            </div>
        </body>
        </html>
        """
        
        return html_content


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
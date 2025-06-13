import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime
import re


# Configure Gemini API
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

# Configure page
st.set_page_config(
    page_title="AI Feedback Generator",
    page_icon="🎓",
    layout="wide"
)

# Initialize session state
if 'feedback_history' not in st.session_state:
    st.session_state.feedback_history = []

# Sample rubric templates
SAMPLE_RUBRICS = {
    "Internal Assessment 1": {
        "criteria": {
            "AI (Artificial Intelligence)": {"weight": 20, "max_score": 4},
            "ML (Machine Learning)": {"weight": 20, "max_score": 4},
            "DL (Deep Learning)": {"weight": 20, "max_score": 4},
            "Stats (Statistics)": {"weight": 20, "max_score": 4},
            "Python Programming": {"weight": 20, "max_score": 4}
        },
        "performance_levels": {
            4: "Excellent",
            3: "Good", 
            2: "Satisfactory",
            1: "Needs Improvement"
        }
    },
    "Internal Assessment 2": {
        "criteria": {
            "AI (Artificial Intelligence)": {"weight": 20, "max_score": 4},
            "ML (Machine Learning)": {"weight": 20, "max_score": 4},
            "DL (Deep Learning)": {"weight": 20, "max_score": 4},
            "Stats (Statistics)": {"weight": 20, "max_score": 4},
            "Python Programming": {"weight": 20, "max_score": 4}
        },
        "performance_levels": {
            4: "Excellent",
            3: "Good",
            2: "Satisfactory", 
            1: "Needs Improvement"
        }
    }
}

# Feedback templates
FEEDBACK_TEMPLATES = {
    "constructive": """
    You are an encouraging and constructive educator providing personalized feedback to a student.
    
    Based on the rubric performance data, generate feedback that:
    - Acknowledges specific strengths
    - Provides actionable suggestions for improvement
    - Maintains an encouraging and supportive tone
    - Includes specific examples when possible
    - Offers concrete next steps
    
    Keep the feedback between 150-250 words and make it personal and motivating.
    """,
    
    "detailed": """
    You are a thorough educator providing comprehensive feedback to a student.
    
    Based on the rubric performance data, generate detailed feedback that:
    - Analyzes each criterion thoroughly
    - Provides specific examples of what was done well
    - Offers detailed suggestions for improvement
    - Connects performance to learning objectives
    - Includes resources or strategies for growth
    
    Keep the feedback between 250-400 words and make it thorough yet accessible.
    """,
    
    "brief": """
    You are an efficient educator providing concise feedback to a student.
    
    Based on the rubric performance data, generate brief feedback that:
    - Highlights key strengths and areas for improvement
    - Provides 2-3 specific actionable suggestions
    - Maintains a positive and encouraging tone
    - Is clear and easy to understand
    
    Keep the feedback between 75-150 words and make it punchy and memorable.
    """
}

def generate_feedback(student_name,rubric_data, scores, feedback_style="constructive"):
    """Generate personalized feedback using Gemini API"""
    
    # Prepare rubric performance summary
    performance_summary = []
    total_score = 0
    max_possible = 0
    
    for criterion, details in rubric_data['criteria'].items():
        score = scores.get(criterion, 0)
        max_score = details['max_score']
        weight = details['weight']
        performance_level = rubric_data['performance_levels'].get(score, "Not Assessed")
        
        performance_summary.append(f"- {criterion}: {score}/{max_score} ({performance_level})")
        total_score += score * (weight / 100)
        max_possible += max_score * (weight / 100)
    
    performance_text = "\n".join(performance_summary)
    overall_percentage = (total_score / max_possible) * 100 if max_possible > 0 else 0
    
    # Construct prompt
    prompt = f"""
    {FEEDBACK_TEMPLATES[feedback_style]}
    
    Student: {student_name}
    Overall Score: {total_score:.1f}/{max_possible:.1f} ({overall_percentage:.1f}%)
    
    Performance by Criteria:
    {performance_text}
    
    Generate personalized feedback for this student's performance.
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        return response.text.strip()
    
    except Exception as e:
        return f"Error generating feedback: {str(e)}"

def calculate_overall_score(rubric_data, scores):
    """Calculate weighted overall score"""
    total_score = 0
    max_possible = 0
    
    for criterion, details in rubric_data['criteria'].items():
        score = scores.get(criterion, 0)
        max_score = details['max_score']
        weight = details['weight']
        
        total_score += score * (weight / 100)
        max_possible += max_score * (weight / 100)
    
    return total_score, max_possible

def main():
    st.title("🎓 GradeCraft – crafted feedback for student assessments")
    st.markdown("Generate personalized, consistent feedback for student assessments using AI")
    
    # Sidebar for feedback history
    with st.sidebar:
        st.header("📊 Feedback History")
        if st.session_state.feedback_history:
            for i, entry in enumerate(reversed(st.session_state.feedback_history[-5:])):
                with st.expander(f"{entry['student']}..."):
                    st.write(f"**Score:** {entry['score']:.1f}/{entry['max_score']:.1f}")
                    st.write(f"**Date:** {entry['date']}")
        else:
            st.info("No feedback generated yet")
    
    # Main interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📋 Setup Evaluation Criteria")
        
        # Student and assignment info
        student_name = st.text_input("Student Name", placeholder="Enter student's name")
        #assignment_name = st.text_input("Assignment Name", placeholder="Enter assignment name")
        
        # Rubric selection
        st.subheader("Rubric Selection")
        rubric_choice = st.selectbox("Choose a rubric template", list(SAMPLE_RUBRICS.keys()))
        
        # Option to create custom rubric
        if st.checkbox("Create Custom Rubric"):
            st.subheader("Custom Rubric Builder")
            custom_criteria = {}
            
            num_criteria = st.number_input("Number of Criteria", min_value=1, max_value=10, value=3)
            
            for i in range(num_criteria):
                with st.expander(f"Criterion {i+1}"):
                    criterion_name = st.text_input(f"Criterion Name {i+1}", key=f"crit_name_{i}")
                    weight = st.number_input(f"Weight (%)", min_value=1, max_value=100, value=25, key=f"weight_{i}")
                    max_score = st.number_input(f"Max Score", min_value=1, max_value=10, value=4, key=f"max_{i}")
                    
                    if criterion_name:
                        custom_criteria[criterion_name] = {"weight": weight, "max_score": max_score}
            
            if custom_criteria:
                total_weight = sum(details['weight'] for details in custom_criteria.values())
                if total_weight != 100:
                    st.warning(f"Total weight is {total_weight}%. Should equal 100%.")
                else:
                    selected_rubric = {
                        "criteria": custom_criteria,
                        "performance_levels": {4: "Excellent", 3: "Good", 2: "Satisfactory", 1: "Needs Improvement"}
                    }
            else:
                selected_rubric = SAMPLE_RUBRICS[rubric_choice]
        else:
            selected_rubric = SAMPLE_RUBRICS[rubric_choice]
        
        # Display selected rubric
        st.subheader("Selected Rubric")
        for criterion, details in selected_rubric['criteria'].items():
            st.write(f"**{criterion}:** {details['weight']}% weight, Max score: {details['max_score']}")
    
    with col2:
        st.header("📊 Student Performance Input")
        
        # Score input
        scores = {}
        for criterion, details in selected_rubric['criteria'].items():
            score = st.selectbox(
                f"{criterion} (Weight: {details['weight']}%)",
                range(0, details['max_score'] + 1),
                key=f"score_{criterion}"
            )
            scores[criterion] = score
        
        # Calculate overall score
        total_score, max_possible = calculate_overall_score(selected_rubric, scores)
        overall_percentage = (total_score / max_possible) * 100 if max_possible > 0 else 0
        
        st.metric("Overall Score", f"{total_score:.1f}/{max_possible:.1f}", f"{overall_percentage:.1f}%")
        
        # Feedback style selection
        st.subheader("Feedback Style")
        feedback_style = st.selectbox(
            "Choose feedback style",
            ["constructive", "detailed", "brief"],
            format_func=lambda x: x.title()
        )
        
        # Generate feedback button
        if st.button("🤖 Generate AI Feedback", type="primary"):
            if not student_name :
                st.error("Please enter student name and assignment name")
            else:
                with st.spinner("Generating personalized feedback..."):
                    feedback = generate_feedback(
                        student_name,  
                        selected_rubric, scores, feedback_style
                    )
                
                # Display feedback
                st.subheader("Generated Feedback")
                st.write(feedback)
                
                # Save to history
                st.session_state.feedback_history.append({
                    'student': student_name,
                    #'assignment': assignment_name,
                    'score': total_score,
                    'max_score': max_possible,
                    'feedback': feedback,
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                
                # Download option
                feedback_text = f"""
Student: {student_name}
Score: {total_score:.1f}/{max_possible:.1f} ({overall_percentage:.1f}%)
Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}

Feedback:
{feedback}
"""
                st.download_button(
                    "📥 Download Feedback",
                    feedback_text,
                    file_name=f"{student_name}feedback.txt",
                    mime="text/plain"
                )
    
    # Batch processing section
    st.header("📋 Batch Processing")
    st.markdown("Upload a CSV file with student data for batch feedback generation")
    
    uploaded_file = st.file_uploader("Choose CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.subheader("Preview Data")
            st.dataframe(df.head())
            
            # Expected columns info
            st.info("Expected columns: student_name, assignment_name, and score columns matching your rubric criteria")
            
            if st.button("Generate Batch Feedback"):
                progress_bar = st.progress(0)
                batch_results = []
                
                for i, row in df.iterrows():
                    # Extract scores for rubric criteria
                    batch_scores = {}
                    for criterion in selected_rubric['criteria'].keys():
                        if criterion.lower().replace(' ', '_') in row:
                            batch_scores[criterion] = row[criterion.lower().replace(' ', '_')]
                    
                    if batch_scores and 'student_name' in row and 'assignment_name' in row:
                        feedback = generate_feedback(
                            row['student_name'], row['assignment_name'],
                            selected_rubric, batch_scores, feedback_style
                        )
                        batch_results.append({
                            'Student': row['student_name'],
                            'Assignment': row['assignment_name'],
                            'Feedback': feedback
                        })
                    
                    progress_bar.progress((i + 1) / len(df))
                    
                    if batch_results:
                        results_df = pd.DataFrame(batch_results)
                        st.subheader("Batch Results")
                        st.dataframe(results_df)
                        
                        # Download batch results
                        csv = results_df.to_csv(index=False)
                        st.download_button(
                            "📥 Download Batch Results",
                            csv,
                            file_name="batch_feedback_results.csv",
                            mime="text/csv"
                        )
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()

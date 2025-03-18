from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
import pandas as pd
import pickle
import json
import os
import random

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session


api_key = os.environ.get("DEEPSEEK_API_KEY", "sk-1a27d4ea17a2449f96897f8cc0e02875")
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# List of majors to recommend
majors = [
    "BACHELOR OF ARTS IN MASS COMMUNICATION",
    "BACHELOR OF SCIENCE IN BIOTECHNOLOGY",
    "BACHELOR OF SCIENCE IN BUSINESS ADMINISTRATION",
    "BACHELOR OF ARCHITECTURE",
    "BACHELOR OF ARTS IN INTERIOR DESIGN",
    "BACHELOR OF SCIENCE IN ARTIFICIAL INTELLIGENCE",
    "BACHELOR OF SCIENCE IN CHEMICAL ENGINEERING",
    "BACHELOR OF SCIENCE IN CIVIL AND INFRASTRUCTURE ENGINEERING",
    "BACHELOR OF SCIENCE IN COMPUTER ENGINEERING",
    "BACHELOR OF SCIENCE IN COMPUTER SCIENCE",
    "BACHELOR OF SCIENCE IN ELECTRICAL AND ELECTRONICS ENGINEERING",
    "BACHELOR OF SCIENCE IN MECHANICAL ENGINEERING",
    "BACHELOR OF SCIENCE IN PETROLEUM ENGINEERING"
]

# Define the list of questions
questions = [
    "Which high school curriculum did you follow?",
    "Which subjects did you study in high school?",
    "What was your IELTS/TOEFL score?",
    "Which field interests you the most?",
    "What type of career do you envision?",
    "Do you prefer a technical, creative, or business-oriented role?",
    "Would you like to work in a research, corporate, startup, or freelance environment?",
    "How important is job stability in your career choice?",
    "Do you prefer working with people or working with technology?",
    "Do you enjoy working on structured tasks with clear guidelines?",
    "Do you enjoy hands-on work (e.g., lab experiments, building things)?",
    "Do you prefer theoretical learning, practical work, or a mix of both?",
    "Would you rather work on individual projects or team-based assignments?",
    "Do you prefer exams, projects, or research-based assessments?",
    "How comfortable are you with subjects like math and science?",
    "Are you looking for a flexible program where you can specialize later?",
    "Would you prefer a structured degree (e.g., Computer Science, Biotechnology) or one with multiple pathways (e.g., Business, Media)?",
    "Would you like a program with strong industry connections and internship opportunities?",
    "Do you see yourself working in an office, lab, outdoors, or remotely?",
    "Do you want a job with a predictable routine or a dynamic work environment?",
    "How important is global career mobility for you?",
    "Do you want a career that allows remote work?"
]

def get_major_recommendation(answers):
    # Format answers as a string with question-answer pairs
    formatted_answers = "\n".join([f"Q: {q}\nA: {a}" for q, a in answers.items()])
    
    prompt = f"""
    Based on the following survey answers, recommend the most suitable university major from this list:
    {', '.join(majors)}
    
    Consider the student's interests, preferences, and aptitudes as shown in their responses.
    
    Survey responses:
    {formatted_answers}
    
    Return a full report that analyze why this major is important and what are the possible job opprotuinites and field of work that they might get , in nice way without any upper cases and in and in an easy languge in both arabic and english (dont explcitly mention the language).
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a career guidance counselor specializing in recommending university majors based on student preferences and aptitudes."},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content
        else:
            # Fallback to random major if API fails
            return random.choice(majors)
    
    except Exception as e:
        print(f"Error getting recommendation: {e}")
        # Fallback to random major if API fails
        return random.choice(majors)

def extract_preferences(answers):
    # This function will extract key preferences to display to the user
    prompt = """
    Based on the following survey answers, extract 5-7 key preferences or traits of this student.
    Format the response as a simple JSON with feature names as keys and values like "High", "Medium", "Low" or specific preferences.
    For example:
    {
        "analytical_thinking": "High",
        "creativity": "Medium",
        "preferred_environment": "Corporate",
        "math_ability": "Strong",
        "likes_teamwork": "Yes"
    }
    Only return the JSON without additional text.
    """
    
    try:
        # Format answers as a string with question-answer pairs
        formatted_answers = "\n".join([f"Q: {q}\nA: {a}" for q, a in answers.items()])
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You extract structured information from survey responses."},
                {"role": "user", "content": f"Survey Responses:\n{formatted_answers}\n\n{prompt}"}
            ],
            stream=False
        )
        
        if response.choices and response.choices[0].message.content:
            # Try to parse as JSON, fallback to empty dict if parsing fails
            try:
                return json.loads(response.choices[0].message.content)
            except:
                return {}
        else:
            return {}
    
    except Exception as e:
        print(f"Error extracting preferences: {e}")
        return {}

def prepare_features(responses):
    # Convert responses to DataFrame format
    df = pd.DataFrame([responses])
    features_scaled = [[0.5] * 10]  
    return features_scaled

@app.route('/')
def home():
    # Initialize or reset session data
    session['answers'] = {}
    session['current_question'] = 0
    session['chat_history'] = []
    return render_template('index.html')

@app.route('/start_chat', methods=['GET'])
def start_chat():
    # Reset session variables
    session['answers'] = {}
    session['current_question'] = 0
    session['chat_history'] = []
    
    # Add welcome message
    welcome_message = {
        "sender": "bot",
        "message": "Welcome to the Career Guidance Survey! I'll ask you a series of questions to help recommend suitable career paths. Let's begin with the first question:",
        "isQuestion": False
    }
    
    # Add first question
    first_question = {
        "sender": "bot",
        "message": questions[0],
        "isQuestion": True
    }
    
    session['chat_history'] = [welcome_message, first_question]
    
    return jsonify({
        "history": session['chat_history'],
        "currentQuestion": 0,
        "totalQuestions": len(questions)
    })

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    user_message = data['message'].strip()
    current_question = session.get('current_question', 0)
    
    if not user_message:
        return jsonify({
            "error": "Please provide an answer"
        }), 400
    
    # Add user message to chat history
    chat_history = session.get('chat_history', [])
    chat_history.append({
        "sender": "user",
        "message": user_message,
        "isQuestion": False
    })
    
    # Store the answer
    answers = session.get('answers', {})
    answers[questions[current_question]] = user_message
    session['answers'] = answers
    
    # Update current question
    current_question += 1
    session['current_question'] = current_question
    
    # Check if we've reached the end of questions
    if current_question >= len(questions):
        # Survey completed
        chat_history.append({
            "sender": "bot",
            "message": "Thank you for completing all the questions! I'm processing your responses now...",
            "isQuestion": False
        })
        

        extracted_preferences = extract_preferences(answers)
        
        # Get recommendation from API
        recommendation = get_major_recommendation(answers)
        

        # Add results to chat
        result_message = f"Based on your responses, I recommend: {recommendation}\n\n\n"
        for key, value in extracted_preferences.items():
            result_message += f"• {key}: {value}\n"
        
        chat_history.append({
            "sender": "bot",
            "message": result_message,
            "isQuestion": False
        })
        
        # Save updated chat history
        session['chat_history'] = chat_history
        
        return jsonify({
            "history": chat_history,
            "completed": True,
            "prediction": recommendation,
            "extractedData": extracted_preferences
        })
    else:
        # Send next question
        chat_history.append({
            "sender": "bot",
            "message": questions[current_question],
            "isQuestion": True
        })
        
        # Save updated chat history
        session['chat_history'] = chat_history
        
        return jsonify({
            "history": chat_history,
            "currentQuestion": current_question,
            "totalQuestions": len(questions),
            "completed": False
        })

@app.route('/get_chat_history', methods=['GET'])
def get_chat_history():
    chat_history = session.get('chat_history', [])
    current_question = session.get('current_question', 0)
    
    return jsonify({
        "history": chat_history,
        "currentQuestion": current_question,
        "totalQuestions": len(questions),
        "completed": current_question >= len(questions)
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
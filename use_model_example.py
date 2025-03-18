
    # Example code to use the saved model
    import joblib
    import pandas as pd
    
    # Load the model
    model = joblib.load("major_prediction_model.joblib")
    
    # Prepare input data (must have the same columns as training data)
    # Replace with your actual column names
    sample_data = pd.DataFrame({
        'math_score': [85],
        'science_score': [92],
        'english_score': [78],
        # Add all required columns here
    })
    
    # Make prediction
    predicted_major = model.predict(sample_data)[0]
    print(f"Recommended major: {predicted_major}")
    
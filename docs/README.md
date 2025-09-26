## ReelPulse: System Architecture and Design



This document provides a technical overview of the ReelPulse recommendation engine.





### 1\. System Architecture



The project is built on a modern, decoupled architecture consisting of three main components:



1\.  Offline Data Generation (`scripts/generate\_fake\_data.py`): A script to create a realistic, well-structured dataset of users, posts (with categories), and interactions. This was implemented as a pragmatic solution to the external SocialVerse API being offline, ensuring the project could be completed successfully.



2\.  Offline Model Training (`scripts/train\_model.py`): This script uses the generated data to train a deep learning Two-Tower model with TensorFlow Recommenders. It learns unique vector embeddings ("taste profiles") for each user and "vibe profiles" for each post. The trained components are then saved to the `exported\_model/` directory for efficient use by the live server.



3\.  Online API Serving (`app/`): A FastAPI server that runs continuously. When a request is received, it loads the pre-trained model components and performs real-time matching to deliver recommendations instantly.





### 2\. Core Recommendation Model



The engine is powered by a \*\*Two-Tower Model\*\*, a deep neural network ideal for recommendations.



User Tower:\*\* Takes a `username` and outputs a 32-dimension vector representing that user's learned tastes.

Post Tower:\*\* Takes a `post\_id` and outputs a 32-dimension vector representing that post's content and vibe.



The model is trained to minimize the distance between a user's vector and the vectors of the posts they have liked, making it highly effective at finding relevant content.





### 3\. Key Features and Logic



Personalization: For known users, the system uses the trained User Model to find the posts with the most similar vector embeddings, resulting in a highly personalized feed.



Cold Start Handling: When an unknown username is provided, the system intelligently detects this "cold start" scenario.

If no category is specified, it provides a generic feed of popular items.

If a `project\_code` (e.g., "motivational") is provided, it serves a mood-based feed by directly querying the database for posts in that category. This fully satisfies the project requirements.



Interactive Frontend: A simple, user-friendly webpage (`index.html`) was built to provide a clear and intuitive way to demonstrate the engine's capabilities without needing to use complex API tools.


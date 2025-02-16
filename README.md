# Medical Task Assistant Robot
---

## Project Purpose

The **Autonomous Medication Distribution Robot** focuses on the following key objectives:

### 1. Medication Distribution
- A pill-dispensing system allows the robot to deliver the correct dosage to patients as per instructions.
- The robot will autonomously navigate hospital environments to reach designated rooms.

### 2. Patient Health Monitoring
- Integrated health-monitoring sensors measure patient metrics such as:
  - Oxygen levels
  - Blood pressure
  - Body temperature
- These metrics can be used for real-time monitoring and future AI-driven personalization.

- ### 3. Reliable Communication & Control
- Communication between the robot and the system relies on:
  - Wi-Fi for real-time updates
  - SSH for remote access
  - Wired connections for initial setups and data transfer
- Ensures smooth operation and high reliability in hospital settings.

### 4. Future Enhancements
- AI-driven pill scheduling and distribution based on patient health data for personalized care plans.

### 5. Diagrams
- BPM Diagram:
![BPM Diagram](docs/bpm.png)

### 6. Model Info

- The files for creation of model is in the Model folder in github. There are 2 files for training the Model (i) "Gpt-v1.ipynb", (ii) "training.py" and iii) 'extraction' is used for conversion of dataset.
- The original site for dataset used in training process is 'https://huggingface.co/datasets/Skylion007/openwebtext' but we couldn't find the file there so had to do other research.
- The actual site from where I have downloaded the data set (OpenWebText) is refered in Basecamp reference section.
- The zip file of Openwebtex is then extracted and it is in .xz format.
- Our extraction.py file is used to convert the .xz format file into .txt file. Make sure you have installed "tqdm" library for python to run the extraction.py file. **Condition to run this is you must have python version 3.9.12 because "lzma" or "pylzma" is only available below 3.9.12 version of python.
- Then 3 files will be extracted from extraction.py "train_split.txt", "val_split.txt" and "vocab.txt". Make sure to save them in folder named as 'train' so it will be easier for you to understand it.
- Now we are installing the pytorch with cuda with this command "pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126"
- Here, we will see some changes in "Gpt-v1.ipynb" and "training.py" those are 'n_head' and 'n_layer', where 1 is the minimum and 8 is the maximum you can keep so that it doesn't affect your GPU more.
- If you are using "training.py" file remove these lines at first (212,213,214) because i have inserted that line after training the model once. SO if you had traoned  your model once you can add those lines again so that you can re-train the model by using the pre-trained model.
- If you are using the "Gpt-v1.ipynb" remove the (second-last,third-last and forth-last ) lines from second-last cell.
- The information of integrating the model with chatbot is comming soon..........

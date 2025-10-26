# Knighthacks 2025 Project
 Setting up the project environment for Google ADK 

# Step 1
Create environemnt 
```bash
python -m venv .venv
```

# Step 2
activate the enviornment
```bash
.venv\Scripts\activate.bat
```

# Step 3
cd into the folder

# Step 4
run 
```bash
pip install google-adk
```

# Step 5
run 
```bash
adk create <agent_folder_Name>
```

# Step 6
```bash
pip install -r requirements.txt
```

# Step 7 
install the dependencies
Run 
```bash
adk web 
```
and click the localhost link to talk to agent

# How to run the program 
in the directory of the program, cd into the backend folder that hosts the agents and then run
```bash
adk web 
```
then the program should respond

# How to run api server (for testing python code with agents)
1. in the terminal go to a folder that contains agent folder
2. type "adk api_server"
3. open another terminal (without closing previous)
4. go to folder containing app.py and run "python app.py"
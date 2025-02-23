little fun python app for local ollama server chat. this uses the default local ollama server port etc. if you have a different port or ip address for you local ollama server update it in the local-ai-chat.py file. i have uploaded all build files etc and the stand alone mac os app which i have tesed on mac os 15.3.1 i built this with python v 3.12.9 and also installed flet for the gui.. pip3 install flet (copy paste into terminal). i also installed pip... python3 -m ensurepip --upgrade... i am very new at making apps and this is my first attempt. i would like to make a coding local app to similar to cursor ai but all from ollama local ai... its a fun time we live in i hope anyone finds this little app interesting or even make it better with more features etc.. thanks for looking..
also feel free to change the names thats used in the chat just makes it a little more personal lol this is in the local-ai-chat.py file  
# Initialize ref values
        self.user_name.value = "Danny"
        self.ai_thinking_message.value = "🤔 Ron Ai is thinking..."
        self.chat_sessions.value = []
        self.current_chat_id.value = None

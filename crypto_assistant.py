from openai import OpenAI
import json
import time

# Variable for OpenAI API key
OPENAI_API_KEY = "OPENAI_KEY_PLACEHOLDER"

# Assistant class
class CryproTrading_Assistant:

    def __init__(self, assistants_instructions, model, use_rag=False,paths_to_rag_files=[], verbose=False):
        
        self.client = OpenAI( api_key = OPENAI_API_KEY)
        self.verbose = verbose
        self.attached_files = set()
        self.tools = [{
            "type": "function",
            "function": {
              "name": "get_detailed_crypto_data",
              "description": "Get the current price of a cryptocurrency",
              "parameters": {
                "type": "object",
                "properties": {
                  "cryptocurrency": {"type": "string", "description": "The name of the cryptocurrency to extract information."},
                },
                "required": ["cryptocurrency"]
              }
            } 
          },
            {
            "type": "function",
            "function": {
              "name": "get_crypto_news",
              "description": "Get recent published web articles of a cryptocurrency",
              "parameters": {
                "type": "object",
                "properties": {
                  "news_api_url": {"type": "string", "description": "News API URL for the specific cryptocurrency to extract web article information."},
                },
                "required": ["news_api_url"]
              }
            } 
          }
          ]
        
        # Upload and attach files to assistant for Retrieval 
        if use_rag==True:
            self.tools.append({"type": "retrieval"})
            # Upload a file with an "assistants" purpose
            for rag_file in paths_to_rag_files:
                file = self.client.files.create(
                  file=open(rag_file, "rb"),
                  purpose='assistants'
                )
                self.attached_files.add(file.id)

              
        ## CREATING A THREAD, CAN ADD FURTHER INSTRUCTIONS
        self.thread = self.client.beta.threads.create()
        # Create the assistant
        self.assistant = self.client.beta.assistants.create(
          name="Cryptocurrency Expert",
          instructions=assistants_instructions,
          model=model,
          tools=self.tools,
            file_ids=list(self.attached_files)
        )

        print("CryptoTrading Assistant initialized!")
        
    
    # Show the contents of thread
    def show_previous_conversation(self):
        try:
            assistant.thread_messages.data
            while True:
                show_previous_conversation = input("Previous conversation exists, should it be displayed? y/n")
                if show_previous_conversation=="y":
                    ## PRINT THE RESPONSE OF THE LATEST MESSAGE FROM A THREAD
                    for message in assistant.thread_messages.data[::-1]:
                        # print(thread_messages.data[0].content[0].text.value)
                        if message.role=="user":
                            print(message.role.capitalize() + ": " + message.content[0].text.value)
                        else:
                            print("CryptoTrading Assistant: \n" + message.content[0].text.value)
                            print("---------------------------------------------------------------------")
                            print("---------------------------------------------------------------------")
                    return
                elif show_previous_conversation=="n":
                    return
                else:
                    pass
        except:
            return
    
    # Main functionality of the assistant
    def start(self):
        self.show_previous_conversation()

        message = input("User: ")
        while message!="exit":
            ## ADD A MESSAGE TO A THREAD
            message = self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=message
            )

            ## RUN A THREAD WITH THE SPECIFIED ASSISTANT, MESSAGES MUST BE PROVIDED BEFORE RUNNING
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id
            )

            ## GET CURRENT STATUS OF A RUN OF A SPECIFIC THREAD
            while run.status=="queued" or run.status=="in_progress":
                if self.verbose:
                    print(run.status)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=run.id
                )
                time.sleep(2)

            ## Action required -> call functions to collect data
            while run.required_action!=None and run.status=="requires_action":
                tool_outputs = []
                for i in range(len(run.required_action.submit_tool_outputs.tool_calls)):
                    tool_call_id = run.required_action.submit_tool_outputs.tool_calls[i]
                    function_name = run.required_action.submit_tool_outputs.tool_calls[i].function.name
                    function_arguments = json.loads(run.required_action.submit_tool_outputs.tool_calls[i].function.arguments)
                    function_arguments = list(function_arguments.values())
                    if self.verbose:
                        print(function_name + "\n" + function_arguments[0])

                    function_response = globals()[function_name](function_arguments)
                    tool_outputs.append({
                            "tool_call_id": tool_call_id.id,
                            "output": json.dumps(function_response)
                        }
                    )

                run = self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=self.thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
                ## GET CURRENT STATUS OF A RUN OF A SPECIFIC THREAD
                while run.status=="queued" or run.status=="in_progress":
                    run = self.client.beta.threads.runs.retrieve(
                        thread_id=self.thread.id,
                        run_id=run.id
                    )
                    time.sleep(2)
                    if self.verbose:
                        print(run.status)

            self.thread_messages = self.client.beta.threads.messages.list(self.thread.id)
            print("CryptoTrading Assistant:")
            print(self.thread_messages.data[0].content[0].text.value)
            print("---------------------------------------------------------------------")
            print("---------------------------------------------------------------------")
                
            
            message = input("User: ")
        return
    
    # List the files uploaded on OpenAI website and the attached files to the assistant
    def list_rag_files(self,print_files=True):
        assistant_list_of_files_id = []
        if self.client.files.list():
            if print_files:
                for file in self.client.files.list():
                    print("File uploaded to OpenAI RAG: ", file.filename, " with file id: ", file.id)
            
            for file in self.attached_files:
                if print_files:
                    print("File attached to Assistant with id: ", file)
                assistant_list_of_files_id.append(file)
        else:
            print("No file uploaded for RAG")
        
        return assistant_list_of_files_id
    
    # Attach files to assistant
    def attach_uploaded_file_to_assistant(self,files_id):
        ## files_id: list of strings
        ## if retrieval is not enabled already add it to the tools to enable it
        if len(self.tools)==2:
            self.tools.append({"type": "retrieval"})
            self.assistant = self.client.beta.assistants.update( assistant_id=self.assistant.id,
                  tools=self.tools
            )
        # Add the uploaded file to the assistant
        for file_id in files_id:
            self.client.beta.assistants.files.create(assistant_id=self.assistant.id, file_id=file_id)
            self.attached_files.add(file_id)
            
        self.assistant = self.client.beta.assistants.update(assistant_id=self.assistant.id,
            file_ids = files_id
            )
        return 
    # Remoce files from assistant
    def remove_file_from_assistant(self,files_id, disable_rag=False):
        if len(self.tools)==3 and disable_rag:
            self.tools = self.tools[:2]
            self.assistant = self.client.beta.assistants.update(assistant_id=self.assistant.id,
                  tools=self.tools
            )
        for file_id in files_id:
            # Add the uploaded file to the assistant
            try:
                self.client.beta.assistants.files.delete(assistant_id=self.assistant.id, file_id=file_id)
                self.attached_files.remove(file_id)
            except Exception as error:
                # handle the exception
                print(error)
        self.assistant = self.client.beta.assistants.update( assistant_id=self.assistant.id,
            file_ids = list(self.attached_files)
            )
        return 
    
    # Delete thread and assistant
    def delete_assistant_and_thread(self):
        try:
            for file_id in list_rag_files(True):
                response = remove_file_from_assistant(file_id)
                print(response)
        except:
            pass

        response = self.client.beta.threads.delete(self.thread.id)
        print(response)
        response = self.client.beta.assistants.delete(self.assistant.id)
        print(response)

        return
        
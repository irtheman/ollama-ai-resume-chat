from os import getenv, environ
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables.base import RunnableBinding
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_ollama import OllamaLLM, OllamaEmbeddings

class ResumeAgent:
    def __init__(self, agent_type, job_summary, resume_path="./sample_resume.pdf", llm_model="llama3.2:latest", llm_embed="nomic-embed-text"):
        ollama_host = getenv("OLLAMA_HOST")
        if ollama_host is None or ollama_host == "0.0.0.0":
            environ['OLLAMA_HOST'] = "http://127.0.0.1:11434"
                
        self.agent_type = agent_type
        self.job_summary = job_summary
        self.resume_path = resume_path
        self.llm_model = llm_model
        self.llm_embed = llm_embed
        self.chat_history = {}
        self.chat_model = RunnableWithMessageHistory(
            self.create_retrieval_chain(),
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer"
        )

    def create_retrieval_chain(self) -> RunnableBinding:
        # Create a retrieval chain for the agent to query
        llm = OllamaLLM(model=self.llm_model)
        retriever = self.resume_data_loader()
        context_prompt = self.create_contextualized_history_prompt()
        history_aware_retriever = create_history_aware_retriever(llm, retriever, context_prompt)
        qa_prompt = self.create_system_prompt(self.agent_type)
        qa_chain = create_stuff_documents_chain(llm, qa_prompt)
        return create_retrieval_chain(history_aware_retriever, qa_chain)

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        # For RunnableWithMessageHistory, providing a chat history for the current session
        if session_id not in self.chat_history:
            self.chat_history[session_id] = ChatMessageHistory()
        return self.chat_history[session_id]
    
    def resume_data_loader(self):
        # Load and process the resume data
        loader = PyMuPDFLoader(self.resume_path)
        data = loader.load_and_split()
        embeds = OllamaEmbeddings(model=self.llm_embed)
        vectorstore = FAISS.from_documents(data, embeds)
        return vectorstore.as_retriever()

    def create_contextualized_history_prompt(self):
        # Create a prompt to contextualize the chat history
        system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        return ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

    def create_system_prompt(self, type):
        # Create a nire detailed prompt for the system
        if type == "enhance":
            system_prompt = (
                "You are a proficient hiring manager, with vast "
                "experience in reviewing resumes. You will be given "
                "a job summary and the user's resume. Your task is to "
                "analyze the resume in strict fashion and rate it out "
                " of 10 based on job summary. Further suggest improvements in bullet "
                "points to tailor the resume according to job summary. "
                "Do NOT reformat the resume, only give suggestions. "
                "\n\n"
                f"Job Summary: {self.job_summary}"
                "\n\n"
                "You will have additional context which can be "
                "utilized to answer user's queries. "
                "\n\n"
                "Context: {context}"
            )
        else:
            system_prompt = (
                "You are a proficient hiring manager, with vast "
                "experience in interviewing candidates. You will be given "
                "a job summary and the user's resume. Your task is to "
                "interview the user as in a professional setting. "
                "To interview ask a single question at a time. Make sure "
                "the questions are only related to the user's resume. "
                "After the interview is done, tell the user his chances "
                "of getting in with a feedback. "
                "\n\n"
                f"Job Summary: {self.job_summary}"
                "\n\n"
                "You will have additional context which can be "
                "utilized to answer user's queries. "
                "\n\n"
                "Context: {context}"
            )

        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ])
    
    def agent_chat(self, usr_prompt):
        # Have the agent respond to user queries
        return self.chat_model.invoke(
            {
                "input": usr_prompt,
            },
            config={
                "configurable": {"session_id": "acc_setup"}
            }
        )["answer"]

def main():
    chat_agent = ResumeAgent()
    was_used = False
    print("Hi! I'm your resume assistant.")
    print("What would you like to discuss today? ")
    while True:
        prompt = input("Enter your question ('/exit' to quit): ")
        if prompt == "/exit":
            print("I hope I was helpful!") if was_used else print("Thanks for visiting!")
            break
        response = chat_agent.agent_chat(prompt)
        print(f"Assistant: {response}")
        print("-"*30)
        was_used = True

if __name__ == "__main__":
    main()
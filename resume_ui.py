from resume_agent import ResumeAgent
import streamlit as st

def update_resume():
    resume = st.file_uploader("Upload a PDF resume", type="pdf", accept_multiple_files=False)
    if resume is not None:
        with open("./resume.pdf", mode='wb') as w:
            w.write(resume.getvalue())
        return True
    return False

def check_form_state():
    if st.session_state.job_desc == "":
        st.error("Enter a job description")
        return False
    
    if not st.session_state.file_status:
        st.error("Resume not uploaded!")
        return False
    
    if st.session_state.agent_type == "---":
        st.error("Choose a chat option!")
        return False
    
    st.session_state.start_chat = True
    return True

def main():
    if "file_status" not in st.session_state:
        st.session_state.file_status = False
    
    if "start_chat" not in st.session_state:
        st.session_state.start_chat = False
    
    if "job_desc" not in st.session_state:
        st.session_state.job_desc = ""
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "agent" not in st.session_state:
        st.session_state.agent = None
    
    if "agent_type" not in st.session_state:
        st.session_state.agent_type = "---"
        
    if 'options_disabled' not in st.session_state:
        st.session_state.options_disabled = True
    
    st.set_page_config(
        page_title="Resume AI Chat",
        page_icon="📝",
    )
    
    st.write("# Welcome to Resume AI Chat! 📝")
    st.session_state.job_desc = st.text_area("Enter you job description", placeholder="Full job description...")
    
    if st.session_state.job_desc != "":
        st.session_state.options_disabled = False
    else:
        st.session_state.options_disabled = True
    
    st.session_state.file_status = update_resume()

    chat_type = st.selectbox("Choose preferred chat option", ["---", "Enhance resume", "Simulate interview"], disabled=st.session_state.options_disabled)
    if st.session_state.agent_type != chat_type:
        st.session_state.messages = []
        st.session_state.agent_type = chat_type
        if chat_type == "Enhance resume":
            st.session_state.agent = ResumeAgent("enhance", st.session_state.job_desc, "./resume.pdf")
        elif chat_type == "Simulate interview":
            st.session_state.agent = ResumeAgent("simulate", st.session_state.job_desc, "./resume.pdf")
        else:
            st.session_state.agent = None
        if not st.session_state.agent:
            print("agent is missing!!!")
    
    st.button("Update ⇧", on_click=check_form_state)

    if st.session_state.start_chat:
        # Display chat messages from the history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Accept user input
        if prompt := st.chat_input("How can I help?"):
            # Display the user message in the chat message container
            with st.chat_message("user"):
                st.markdown(prompt)

            response = st.session_state.agent.agent_chat(prompt)

            # Display the assistant response in the chat message container
            with st.chat_message("assistant"):
                st.markdown(response)

            # Add the user message to the chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Add the assistant response to the chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()

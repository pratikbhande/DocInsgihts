import os
import streamlit as st
import uuid
from datetime import datetime
from dotenv import load_dotenv
from agents.router_agent import RouterAgent
from utils.gemini_client import setup_gemini_client
from utils.chat_memory import ChatMemory
import tempfile
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("docinsights.log")
    ]
)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="DocInsights - Document Analysis & Reporting",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = ChatMemory()
if "documents" not in st.session_state:
    st.session_state.documents = {}
if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = None
if "router_agent" not in st.session_state:
    st.session_state.router_agent = None
if "current_report" not in st.session_state:
    st.session_state.current_report = None
if "report_history" not in st.session_state:
    st.session_state.report_history = []

def save_uploaded_file(uploaded_file):
    """Save uploaded file to temporary directory and return file path"""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
            tmp.write(uploaded_file.getbuffer())
            file_path = tmp.name
        
        # Store file info in session state
        file_info = {
            "name": uploaded_file.name,
            "path": file_path,
            "type": uploaded_file.type,
            "size": uploaded_file.size,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        st.session_state.documents[uploaded_file.name] = file_info
        return file_path
    
    except Exception as e:
        logging.error(f"Error saving uploaded file: {e}")
        st.error(f"Error saving uploaded file: {e}")
        return None

def handle_api_key():
    """Handle API key input and setup"""
    with st.sidebar.expander("🔑 API Key Setup", expanded="gemini_client" not in st.session_state):
        api_key = st.text_input("Enter your Google Gemini API Key:", type="password")
        if st.button("Set API Key"):
            if not api_key:
                st.error("Please enter a valid API key")
                return False
            
            try:
                st.session_state.gemini_client = setup_gemini_client(api_key)
                st.session_state.router_agent = RouterAgent(st.session_state.gemini_client)
                st.success("API key set successfully!")
                return True
            except Exception as e:
                logging.error(f"Error setting up Gemini client: {e}")
                st.error(f"Error setting up Gemini client: {e}")
                return False
    
    return st.session_state.gemini_client is not None

def handle_file_upload():
    """Handle file upload section"""
    with st.sidebar.expander("📁 Upload Documents", expanded=True):
        uploaded_file = st.file_uploader("Upload a document", 
                                         type=["csv", "xlsx", "xls", "pdf", "txt", "json", "html"],
                                         help="Upload documents for analysis")
        
        if uploaded_file is not None:
            st.info(f"Processing {uploaded_file.name}...")
            file_path = save_uploaded_file(uploaded_file)
            
            if file_path:
                st.success(f"File {uploaded_file.name} uploaded successfully!")
                
                # Process document with router agent for initial analysis
                if st.session_state.router_agent:
                    with st.spinner("Analyzing document..."):
                        analysis = st.session_state.router_agent.process_document(
                            file_path, 
                            uploaded_file.name,
                            uploaded_file.type
                        )
                        st.session_state.chat_memory.add_system_message(
                            f"Document '{uploaded_file.name}' has been analyzed. Type your queries about the document."
                        )
                        
                        # Display initial analysis
                        if analysis:
                            st.subheader("Initial Document Analysis")
                            st.write(analysis)

def display_document_list():
    """Display list of uploaded documents"""
    with st.sidebar.expander("📑 Your Documents", expanded=True):
        if not st.session_state.documents:
            st.info("No documents uploaded yet.")
            return
        
        for doc_name, doc_info in st.session_state.documents.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{doc_name}**")
                st.caption(f"Uploaded: {doc_info['timestamp']}")
            
            with col2:
                if st.button("Remove", key=f"remove_{doc_name}"):
                    # Remove file
                    try:
                        os.remove(doc_info['path'])
                    except:
                        pass
                    
                    # Remove from session state
                    del st.session_state.documents[doc_name]
                    st.rerun()

def display_chat_interface():
    """Display the chat interface"""
    st.subheader("💬 Chat with your documents")
    
    # Display chat messages
    for message in st.session_state.chat_memory.get_messages():
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    user_query = st.chat_input("Ask about your documents...")
    
    if user_query:
        # Add user message to chat history
        st.session_state.chat_memory.add_user_message(user_query)
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_query)
        
        # Get response from router agent
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if st.session_state.router_agent:
                    response = st.session_state.router_agent.process_query(
                        user_query, 
                        st.session_state.chat_memory
                    )
                    
                    # Check if the response contains a report
                    if "REPORT_START" in response:
                        report_content = response.split("REPORT_START")[1].split("REPORT_END")[0].strip()
                        st.session_state.current_report = report_content
                        
                        # Add report to history
                        report_entry = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "content": report_content
                        }
                        st.session_state.report_history.append(report_entry)
                        
                        # Display regular response without the report part
                        regular_response = response.split("REPORT_START")[0].strip()
                        st.markdown(regular_response)
                        st.success("Report generated! View it in the Reports tab.")
                    else:
                        st.markdown(response)
                    
                    # Add assistant response to chat history
                    st.session_state.chat_memory.add_assistant_message(response)
                else:
                    st.error("Please set up your Gemini API key first.")

def display_report_view():
    """Display report view tab"""
    st.subheader("📊 Generated Reports")
    
    # Check if reports exist
    if not st.session_state.report_history:
        st.info("No reports generated yet. Chat with your documents and request a report to generate one.")
        return
    
    # Report selection
    report_timestamps = [f"{i+1}. {r['timestamp']}" for i, r in enumerate(st.session_state.report_history)]
    selected_report = st.selectbox("Select a report to view:", report_timestamps)
    
    if selected_report:
        report_idx = int(selected_report.split('.')[0]) - 1
        report_content = st.session_state.report_history[report_idx]['content']
        
        # Display report
        st.markdown(report_content)
        
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Export as PDF"):
                st.info("PDF export functionality coming soon")
        
        with col2:
            if st.button("Export as HTML"):
                st.info("HTML export functionality coming soon")

def main():
    """Main application function"""
    # App title
    st.title("DocInsights: Document Analysis & Reporting")
    
    # Handle API key
    if not handle_api_key():
        st.warning("Please set up your Google Gemini API key to continue.")
        return
    
    # Handle file upload
    handle_file_upload()
    
    # Display document list
    display_document_list()
    
    # Tabs for chat and reports
    tab1, tab2 = st.tabs(["💬 Chat & Analysis", "📊 Reports"])
    
    with tab1:
        display_chat_interface()
    
    with tab2:
        display_report_view()

if __name__ == "__main__":
    main()
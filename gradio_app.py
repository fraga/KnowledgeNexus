import gradio as gr
import os
import datetime
import logging
import tempfile
import uuid

# Import required components from our codebase
from db.db_manager import Neo4jManager
from nexus.entity_resolution import EntityResolutionPipeline
from nexus.entity_pipeline import EntityPipeline
from nexus.pipeline import KnowledgeNexusPipeline

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_text_input(text, instructions=""):
    """
    Process text input by saving it as a temporary file and processing it through
    the document pipeline, ensuring consistent handling of all inputs.
    """
    if not text.strip():
        return "No text provided."
        
    logger.info("Processing text input of length %d", len(text))
    db_manager = Neo4jManager()
    db_manager.connect()
    
    try:
        # Create a temporary file with the text content
        temp_dir = os.path.join(os.getcwd(), "knowledge_nexus_files", "originals")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate a unique filename
        file_id = str(uuid.uuid4())
        temp_filename = f"{file_id}_text_input.txt"
        file_path = os.path.join(temp_dir, temp_filename)
        
        # Write the text content to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            if instructions:
                f.write(f"Instructions: {instructions}\n\n")
            f.write(text)
            
        logger.info(f"Saved text input to temporary file: {file_path}")
        
        # Process the file using the document pipeline
        pipeline = KnowledgeNexusPipeline(db_manager)
        document = pipeline.process_document(file_path)
        
        # Construct a detailed output summary
        result = f"Processed text as document: {document.file_name}\n"
        result += f"Document ID: {document.id}\n"
        result += f"Content Type: {document.content_type}\n"
        result += f"Status: {document.conversion_status}\n"
        result += f"Description: {document.description}\n\n"
        result += f"Summary: {document.summary}\n\n"
        result += f"Entities extracted ({len(document.entities)}):\n"
        for entity in document.entities:
            result += f"- {entity}\n"
            
        if document.error_message:
            result += f"\nWarnings/Errors: {document.error_message}\n"
            
        logger.info("Successfully processed text input as document")
        return result
    except Exception as e:
        logger.error("Error processing text input: %s", str(e))
        return f"Error: {str(e)}"
    finally:
        db_manager.close()

def process_document_file(file):
    """
    Process an uploaded document file.
    The file can be an image (jpg, png, etc.) or a text/PDF/etc. file.
    """
    if file is None:
        return "No file uploaded."
        
    logger.info("Processing document file: %s", file.name)
    db_manager = Neo4jManager()
    db_manager.connect()
    
    try:
        pipeline = KnowledgeNexusPipeline(db_manager)
        # Process the uploaded file
        document = pipeline.process_document(file.name)
        
        # Construct a detailed output summary
        result = f"Processed document: {document.file_name}\n"
        result += f"Document ID: {document.id}\n"
        result += f"Content Type: {document.content_type}\n"
        result += f"Status: {document.conversion_status}\n"
        result += f"Description: {document.description}\n\n"
        result += f"Summary: {document.summary}\n\n"
        result += f"Entities extracted ({len(document.entities)}):\n"
        for entity in document.entities:
            result += f"- {entity}\n"
            
        if document.error_message:
            result += f"\nWarnings/Errors: {document.error_message}\n"
            
        logger.info("Successfully processed document file")
        return result
    except Exception as e:
        logger.error("Error processing document file: %s", str(e))
        return f"Error: {str(e)}"
    finally:
        db_manager.close()

# Build the Gradio interface
with gr.Blocks(title="Knowledge Nexus") as demo:
    gr.Markdown("""
    # Knowledge Nexus Web UI
    Process text or documents to extract entities and relationships.
    """)
    
    with gr.Tabs():
        # Text Processing Tab
        with gr.TabItem("Process Text Input"):
            text_input = gr.Textbox(
                label="Enter text",
                lines=10,
                placeholder="Paste or type text here..."
            )
            instructions_input = gr.Textbox(
                label="Instructions (optional)",
                lines=2,
                placeholder="e.g., focus on personal or professional relationships..."
            )
            text_button = gr.Button("Process Text", variant="primary")
            text_output = gr.Textbox(label="Results", lines=15)
            text_button.click(
                fn=process_text_input,
                inputs=[text_input, instructions_input],
                outputs=text_output
            )
        
        # Document Processing Tab
        with gr.TabItem("Process Document File"):
            file_input = gr.File(
                label="Upload a document file",
                file_types=[
                    ".txt", ".pdf", ".docx", ".doc",
                    ".jpg", ".jpeg", ".png", ".gif",
                    ".md", ".rtf"
                ]
            )
            doc_button = gr.Button("Process Document", variant="primary")
            doc_output = gr.Textbox(label="Results", lines=15)
            doc_button.click(
                fn=process_document_file,
                inputs=file_input,
                outputs=doc_output
            )
    
    gr.Markdown("""
    ---
    Built with Gradio for Knowledge Nexus
    """)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",  # Make accessible from other machines
        show_api=False,  # Hide API docs
        share=False  # Don't create a public URL
    ) 
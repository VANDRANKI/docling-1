import os
import glob
import time
from io import StringIO
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams

def sanitize_filename(filename):
    """Clean filename to be safe for all operating systems"""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Replace spaces and dots with underscores (except last dot for extension)
    parts = filename.rsplit('.', 1)
    parts[0] = parts[0].replace(' ', '_').replace('.', '_')
    filename = '.'.join(parts)
    
    # Ensure filename is not too long (max 255 chars including extension)
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF with enhanced options"""
    output_string = StringIO()
    
    # Configure layout analysis parameters
    laparams = LAParams(
        line_margin=0.5,      # Margin between lines
        word_margin=0.1,      # Margin between words
        char_margin=2.0,      # Margin between characters
        boxes_flow=0.5,       # Text flow between boxes
        detect_vertical=True, # Detect vertical text
        all_texts=True       # Extract all texts
    )
    
    try:
        with open(pdf_path, 'rb') as fin:
            extract_text_to_fp(
                fin, 
                output_string,
                laparams=laparams,
                codec='utf-8',
            )
        return output_string.getvalue()
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return None

def convert_pdf_to_markdown(pdf_path, markdown_dir):
    """Convert PDF to markdown using pdfminer.six"""
    if not pdf_path or not os.path.exists(pdf_path):
        print(f"PDF file does not exist: {pdf_path}")
        return None
    
    try:
        print(f"\nStarting conversion of: {pdf_path}")
        
        # Get base name and sanitize it
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        safe_name = sanitize_filename(base_name)
        markdown_path = os.path.join(markdown_dir, f"{safe_name}.md")
        print(f"Will output to: {markdown_path}")
        
        # Print file details
        print("\nFile details:")
        print(f"File size: {os.path.getsize(pdf_path)} bytes")
        print(f"File exists: {os.path.exists(pdf_path)}")
        print(f"File is readable: {os.access(pdf_path, os.R_OK)}")
        
        print("\nExtracting text from PDF...")
        text = extract_text_from_pdf(pdf_path)
        
        if not text:
            print("Failed to extract text from PDF")
            return None
        
        if len(text.strip()) == 0:
            print("Extracted text is empty")
            return None
        
        # Basic markdown formatting
        print("Converting to markdown format...")
        lines = text.split('\n')
        markdown_lines = []
        in_paragraph = False
        
        # Add title block
        markdown_lines.append('---\n')
        markdown_lines.append(f'title: "{safe_name}"\n')
        markdown_lines.append('---\n\n')
        
        for line in lines:
            line = line.strip()
            if line:
                # Try to detect headers
                if any(line.lower().startswith(word) for word in ['abstract', 'introduction', 'conclusion', 'references', 'acknowledgments']):
                    markdown_lines.append(f"\n# {line}\n")
                elif any(line.startswith(str(i) + '.') for i in range(1, 10)):
                    markdown_lines.append(f"\n## {line}\n")
                elif line.isupper() and len(line) > 10:  # Long uppercase lines are likely headers
                    markdown_lines.append(f"\n# {line}\n")
                # References
                elif line.startswith('[') and ']' in line:
                    markdown_lines.append(f"\n{line}\n")
                # Regular text
                else:
                    if in_paragraph:
                        markdown_lines.append(line + ' ')
                    else:
                        markdown_lines.append('\n' + line + ' ')
                        in_paragraph = True
            else:
                if in_paragraph:
                    markdown_lines.append('\n\n')
                    in_paragraph = False
        
        markdown_content = ''.join(markdown_lines)
        
        # Write to file
        print("Writing markdown file...")
        with open(markdown_path, 'w', encoding='utf-8') as fout:
            fout.write(markdown_content)
        
        if os.path.exists(markdown_path):
            print(f"\nSuccessfully converted: {pdf_path}")
            print(f"Output file exists at: {markdown_path}")
            print(f"Output file size: {os.path.getsize(markdown_path)} bytes")
            return markdown_path
        else:
            print(f"\nError: Output file was not created at {markdown_path}")
            return None
    
    except Exception as e:
        import traceback
        print(f"\nError converting {pdf_path}:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        return None

def verify_directory(path, create=False):
    """Verify directory exists and is accessible"""
    abs_path = os.path.abspath(path)
    print(f"\nVerifying directory: {abs_path}")
    
    if os.path.exists(abs_path):
        print(f"Directory exists: {abs_path}")
        if os.path.isdir(abs_path):
            print("Path is a directory")
            if os.access(abs_path, os.R_OK):
                print("Directory is readable")
                if create and os.access(abs_path, os.W_OK):
                    print("Directory is writable")
                return True
            else:
                print("Directory is not readable!")
        else:
            print("Path is not a directory!")
    else:
        print(f"Directory does not exist: {abs_path}")
        if create:
            try:
                os.makedirs(abs_path, exist_ok=True)
                print(f"Created directory: {abs_path}")
                return True
            except Exception as e:
                print(f"Failed to create directory: {e}")
    return False

def main():
    try:
        # Set up directories with absolute paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_dir = os.path.join(current_dir, "Reserach_Papers_PDF", "Ceria_Reserach_Papers")
        markdown_dir = os.path.join(current_dir, "markdown_papers")
        
        print("\nStarting paper processing...")
        
        # Verify directories
        if not verify_directory(pdf_dir):
            print("Error: PDF directory is not accessible!")
            return
        
        if not verify_directory(markdown_dir, create=True):
            print("Error: Cannot create or access markdown directory!")
            return
        
        # List contents of PDF directory
        print("\nContents of PDF directory:")
        try:
            for item in os.listdir(pdf_dir):
                item_path = os.path.join(pdf_dir, item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path)
                    print(f"- {item} ({size} bytes)")
                else:
                    print(f"- {item}/")
        except Exception as e:
            print(f"Error listing directory contents: {e}")
            return
        
        # Clear existing markdown files
        if os.path.exists(markdown_dir):
            print("\nClearing existing markdown files...")
            for file in os.listdir(markdown_dir):
                file_path = os.path.join(markdown_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        print(f"Deleted: {file}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
        
        # Get list of PDF files
        print("\nSearching for PDF files...")
        try:
            pdf_files = []
            for file in os.listdir(pdf_dir):
                if file.lower().endswith('.pdf'):
                    full_path = os.path.join(pdf_dir, file)
                    if os.path.isfile(full_path):
                        pdf_files.append(full_path)
            
            pdf_files.sort()
            total_pdfs = len(pdf_files)
            
            if total_pdfs == 0:
                print(f"No PDF files found in {pdf_dir}")
                return
            
            print(f"\nFound {total_pdfs} PDF files to process:")
            for pdf in pdf_files:
                size = os.path.getsize(pdf)
                print(f"- {os.path.basename(pdf)} ({size} bytes)")
        except Exception as e:
            print(f"Error searching for PDF files: {e}")
            return
        
        # Process all PDFs
        successful = 0
        failed = 0
        error_files = []
        
        for index, pdf_path in enumerate(pdf_files, 1):
            print(f"\n{'='*80}")
            print(f"Processing PDF {index}/{total_pdfs}")
            print(f"File: {os.path.basename(pdf_path)}")
            print('='*80)
            
            try:
                markdown_path = convert_pdf_to_markdown(pdf_path, markdown_dir)
                
                if markdown_path:
                    print(f"Successfully converted to: {markdown_path}")
                    successful += 1
                else:
                    print("Failed to convert PDF to markdown")
                    failed += 1
                    error_files.append(os.path.basename(pdf_path))
                
            except Exception as e:
                print(f"Error processing {pdf_path}:")
                print(f"Error details: {str(e)}")
                failed += 1
                error_files.append(os.path.basename(pdf_path))
                continue
            
            # Add a small delay between files to avoid system overload
            if index < total_pdfs:
                time.sleep(1)
        
        print("\nProcessing complete!")
        print(f"\nResults:")
        print(f"Total PDFs processed: {total_pdfs}")
        print(f"Successfully converted: {successful}")
        print(f"Failed to convert: {failed}")
        
        if error_files:
            print("\nFiles that failed to convert:")
            for file in error_files:
                print(f"- {file}")
        
    except Exception as e:
        import traceback
        print(f"\nCritical error in main process:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()

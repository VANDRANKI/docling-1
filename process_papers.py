import os
import requests
from docling import DocumentConverter
from urllib.parse import quote
import time

# API Keys
ELSEVIER_API_KEYS = [
    "5fac990c4552dc02dad7c61f0c175b21",  # Personal API key
    "70246956c007abe03b277c3161e5cfe5"   # Institutional API key
]

def debug_response(response, prefix=""):
    """Debug helper to print detailed response information"""
    print(f"\n{prefix} Response Details:")
    print(f"Status Code: {response.status_code}")
    print("Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    print("Response Content:")
    try:
        print(response.json())
    except:
        print("Not JSON content")
        print(response.text[:500] + "..." if len(response.text) > 500 else response.text)

def get_pdf_from_doi(doi, output_dir):
    """Download PDF from DOI using Elsevier API"""
    # Clean DOI
    doi = doi.strip()
    if doi.startswith('https://doi.org/'):
        doi = doi[16:]
    
    print(f"\nProcessing DOI: {doi}")
    print("="*80)
    
    # Create filename from DOI
    filename = quote(doi, safe='') + '.pdf'
    output_path = os.path.join(output_dir, filename)
    
    # Skip if already downloaded
    if os.path.exists(output_path):
        print(f"Already downloaded: {doi}")
        return output_path

    # Try each API key
    for api_key in ELSEVIER_API_KEYS:
        print(f"\nTrying with API key: {api_key[:8]}...")
        
        headers = {
            'X-ELS-APIKey': api_key,
            'X-ELS-Insttoken': api_key,  # Some APIs need this for institutional access
            'Accept': 'application/pdf',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            # First try to get entitlements
            print("\nChecking entitlements...")
            entitlements_url = f"https://api.elsevier.com/content/article/entitlement/doi/{doi}"
            entitlements_headers = headers.copy()
            entitlements_headers['Accept'] = 'application/json'
            entitlements_response = requests.get(entitlements_url, headers=entitlements_headers)
            debug_response(entitlements_response, "Entitlements")

            # Get article metadata
            print("\nFetching metadata...")
            metadata_url = f"https://api.elsevier.com/content/article/doi/{doi}"
            metadata_headers = headers.copy()
            metadata_headers['Accept'] = 'application/json'
            metadata_response = requests.get(metadata_url, headers=metadata_headers)
            debug_response(metadata_response, "Metadata")
        
            if metadata_response.status_code == 200:
                try:
                    metadata = metadata_response.json()
                    
                    # Try to get PII first
                    pii = None
                    if 'full-text-retrieval-response' in metadata:
                        pii = metadata['full-text-retrieval-response']['coredata'].get('pii')
                    elif 'coredata' in metadata:
                        pii = metadata['coredata'].get('pii')
                    
                    if pii:
                        print(f"\nFound PII: {pii}")
                        
                        # Try different PDF endpoints
                        pdf_urls = [
                            f"https://api.elsevier.com/content/article/pii/{pii}?httpAccept=application/pdf",
                            f"https://api.elsevier.com/content/article/pii/{pii}/pdf",
                            f"https://api.elsevier.com/content/article/doi/{doi}?httpAccept=application/pdf"
                        ]
                        
                        for pdf_url in pdf_urls:
                            print(f"\nTrying PDF URL: {pdf_url}")
                            pdf_response = requests.get(pdf_url, headers=headers)
                            debug_response(pdf_response, "PDF Download")
                            
                            if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('content-type', '').lower():
                                with open(output_path, 'wb') as f:
                                    f.write(pdf_response.content)
                                print(f"\nSuccessfully downloaded: {doi}")
                                return output_path
                    else:
                        print("\nCould not find PII in metadata")
                        
                    # Try direct DOI download
                    print("\nAttempting direct DOI download...")
                    direct_url = f"https://api.elsevier.com/content/article/doi/{doi}?httpAccept=application/pdf"
                    direct_response = requests.get(direct_url, headers=headers)
                    debug_response(direct_response, "Direct DOI Download")
                    
                    if direct_response.status_code == 200 and 'application/pdf' in direct_response.headers.get('content-type', '').lower():
                        with open(output_path, 'wb') as f:
                            f.write(direct_response.content)
                        print(f"\nSuccessfully downloaded via direct DOI: {doi}")
                        return output_path
                    
                except Exception as e:
                    print(f"\nError processing metadata: {str(e)}")
                    continue
            else:
                print(f"\nError fetching metadata: {metadata_response.status_code}")

        except Exception as e:
            print(f"\nError with API key {api_key[:8]}: {str(e)}")
            continue

    print(f"\nFailed to download {doi} with all API keys")
    return None

def convert_pdf_to_markdown(pdf_path, markdown_dir):
    """Convert PDF to markdown using docling"""
    if not pdf_path or not os.path.exists(pdf_path):
        return None
    
    try:
        # Create converter instance with specific options for better PDF handling
        converter = DocumentConverter()
        
        # Get base name for markdown file
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        markdown_path = os.path.join(markdown_dir, f"{base_name}.md")
        
        # Convert PDF to markdown with enhanced options
        converter.convert(
            pdf_path,
            markdown_path,
            options={
                'pipeline': 'standard_pdf',  # Use standard PDF pipeline
                'ocr_enabled': True,  # Enable OCR for scanned content
                'layout_analysis_enabled': True,  # Better structure preservation
                'table_extraction_enabled': True,  # Extract tables
                'image_extraction_enabled': True,  # Extract images
                'math_extraction_enabled': True,  # Extract mathematical formulas
            }
        )
        
        print(f"Successfully converted: {pdf_path}")
        return markdown_path
    
    except Exception as e:
        print(f"Error converting {pdf_path}: {str(e)}\nStack trace:", exc_info=True)
        return None

def main():
    try:
        # Create directories if they don't exist
        pdf_dir = "downloaded_pdfs"
        markdown_dir = "markdown_papers"
        os.makedirs(pdf_dir, exist_ok=True)
        os.makedirs(markdown_dir, exist_ok=True)
        
        print("\nStarting paper processing...")
        print("PDF directory:", os.path.abspath(pdf_dir))
        print("Markdown directory:", os.path.abspath(markdown_dir))
        
        # Read DOI links
        with open("Reserach_Papers_PDF/Link of the DOI's.txt", 'r', encoding='utf-8') as f:
            doi_links = [line.strip() for line in f if line.strip()]
        
        # For testing, just try the first DOI
        test_doi = doi_links[0]
        print(f"\nTesting with first DOI: {test_doi}")
        
        pdf_path = get_pdf_from_doi(test_doi, pdf_dir)
        
        if pdf_path:
            print(f"\nPDF downloaded successfully to: {pdf_path}")
            print("\nAttempting to convert to markdown...")
            markdown_path = convert_pdf_to_markdown(pdf_path, markdown_dir)
            
            if markdown_path:
                print(f"Successfully converted to: {markdown_path}")
            else:
                print("Failed to convert PDF to markdown")
        else:
            print("\nFailed to download PDF")
        
    except Exception as e:
        print(f"\nCritical error in main process:")
        print(f"Error details: {str(e)}")
        raise

if __name__ == "__main__":
    main()

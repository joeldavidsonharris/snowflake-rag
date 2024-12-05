import argparse
import os
from PyPDF2 import PdfReader, PdfWriter


def split_pdf_into_chunks(input_pdf_path, output_folder, chunk_size=100):
    """
    Splits a PDF into chunks of specified size and saves each chunk as a separate PDF file.

    Args:
        input_pdf_path (str): Path to the input PDF file.
        output_folder (str): Folder to save the output PDF files.
        chunk_size (int): Number of pages per chunk (default is 100).
    """
    # Load the input PDF
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)
    base_name = os.path.basename(input_pdf_path).rsplit('.', 1)[0]

    # Split the PDF into chunks
    for start_page in range(0, total_pages, chunk_size):
        writer = PdfWriter()
        end_page = min(start_page + chunk_size, total_pages)
        
        # Add pages to the writer
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])
        
        # Create the output file name
        output_pdf_path = os.path.join(output_folder, f"{base_name}-pages-{start_page + 1}-to-{end_page}.pdf")
        
        # Write the chunk to a file
        with open(output_pdf_path, "wb") as output_pdf:
            writer.write(output_pdf)

        print(f"Saved chunk: {output_pdf_path}")


def main():
    parser = argparse.ArgumentParser(description="Split PDF files into smaller chunks.")
    parser.add_argument("pdf_files", nargs='+', help="List of PDF files to be split.")
    parser.add_argument("--chunk_size", type=int, default=100, help="Number of pages per chunk (default is 100).")
    args = parser.parse_args()

    output_folder = os.getcwd()

    for pdf_file in args.pdf_files:
        split_pdf_into_chunks(pdf_file, output_folder, args.chunk_size)

if __name__ == "__main__":
    main()

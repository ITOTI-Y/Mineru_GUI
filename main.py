from src.preprocess import PDF2MD

if __name__ == '__main__':
    pdf_path = 'demo.pdf'
    output_dir = 'output'
    pdf2md = PDF2MD(pdf_path)
    pdf2md.run(output_dir=output_dir, parse_method='auto')
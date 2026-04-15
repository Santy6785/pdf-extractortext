from pdf2docx import Converter
from docx2pdf import convert

def pdf_a_word(pdf_path, docx_path): #esta funcion se encarga de converter pdf a word 
    try:
        cv = Converter(pdf_path)
        cv.convert(docx_path)
        cv.close()
        return True
    except Exception as e:
        print("Error en PDF → Word:", e)
        return False

def word_a_pdf(docx_path, pdf_path): #esta otra funcion se encarga de converter word a pdf
    try:
        convert(docx_path, pdf_path)
        return True
    except Exception as e:
        print("Error en Word → PDF:", e)
        return False
    
#pruebas francock

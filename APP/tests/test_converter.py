from converter import pdf_a_word

def test_pdf_a_word():
    resultado = pdf_a_word("test.pdf", "test.docx")
    assert resultado == True
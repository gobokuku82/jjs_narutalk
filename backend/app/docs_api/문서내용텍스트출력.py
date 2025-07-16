from docx import Document

def read_docx_tables(docx_path):
    document = Document(docx_path)
    all_tables = []

    for i, table in enumerate(document.tables):
        table_data = []
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells]
            table_data.append(row_data)
        all_tables.append(table_data)
    
    return all_tables

# 사용 예시
docx_path = "S3/제품설명회_시행_결과보고서.docx"
tables = read_docx_tables(docx_path)

for idx, table in enumerate(tables):
    print(f"\n📌 Table {idx+1}")
    for row in table:
        print(row)
import openpyxl

wb = openpyxl.load_workbook("Composições TCPO - PINI.xlsx", data_only=True)
ws = wb["Composições analíticas"]

print(f"{'Row':<4} | {'Code':<15} | {'Description':<40} | {'Class':<10} | {'Bold':<5} | {'Indent':<6} | {'Leading Spaces'}")
print("-" * 110)

for row_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=100), start=1):
    code_cell = row[0]
    desc_cell = row[1]
    class_cell = row[2]
    
    code_val = code_cell.value
    desc_val = desc_cell.value
    class_val = class_cell.value
    
    if code_val is None and desc_val is None:
        continue
        
    bold_desc = desc_cell.font.bold if desc_cell.font else False
    indent_desc = desc_cell.alignment.indent if desc_cell.alignment else 0
    
    # Check for leading spaces in the description string
    desc_str = str(desc_val) if desc_val is not None else ""
    leading_spaces = len(desc_str) - len(desc_str.lstrip())
    
    # Clean up description for printing
    desc_print = desc_str.strip()
    if len(desc_print) > 37:
        desc_print = desc_print[:34] + "..."
        
    # Only print first 50 rows that actually have content to avoid flooding
    if row_idx < 50:
        print(f"{row_idx:<4} | {str(code_val):<15} | {desc_print:<40} | {str(class_val):<10} | {str(bold_desc):<5} | {str(indent_desc):<6} | {leading_spaces}")

wb.close()

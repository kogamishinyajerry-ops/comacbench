import openpyxl

# Load the input workbook
wb = openpyxl.load_workbook('ssb_455_35_init.xlsx')

# Get the first worksheet
ws = wb.worksheets[0]

# VBA code to delete rows where first character in column B is not 'H' or 'A'
vba_code = '''Sub DeleteRows()
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim i As Long
    Dim firstChar As String
    
    Set ws = ActiveSheet
    lastRow = ws.Cells(ws.Rows.Count, "B").End(xlUp).Row
    
    For i = lastRow To 2 Step -1
        firstChar = Left(ws.Cells(i, "B").Value, 1)
        If firstChar <> "H" And firstChar <> "A" Then
            ws.Rows(i).Delete
        End If
    Next i
End Sub'''

# Write the VBA code into A1:J10411 of Worksheet1
# Split into lines and write across cells
lines = vba_code.split('\n')
row = 1
col = 1
for line in lines:
    ws.cell(row=row, column=col, value=line)
    col += 1
    if col > 10:
        col = 1
        row += 1

# Save as output.xlsx
wb.save('output.xlsx')
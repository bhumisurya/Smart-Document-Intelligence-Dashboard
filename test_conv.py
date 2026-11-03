import os
from document_processor import convert_document

# create a simple txt file
sample_path = 'sample.txt'
with open(sample_path, 'w', encoding='utf-8') as f:
    f.write('Hello world!\n# Heading\n| Col1 | Col2 |\n|---|---|\n| A | B |')

result = convert_document(sample_path)
print('Markdown preview:', result['markdown'][:60])
print('Metadata:', result['metadata'])
print('Stats:', result['stats'])

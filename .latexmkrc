# XeLaTeX is required for Unicode Chinese and the thesis font configuration.
# Keep outputs beside the entry point for Overleaf and local editor compatibility.
$pdf_mode = 5;
$xelatex = 'xelatex %O -interaction=nonstopmode -halt-on-error -file-line-error %S';
$max_repeat = 6;

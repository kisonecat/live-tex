pdfs: $(patsubst %.tex,%.pdf,$(wildcard *.tex))
pngs: $(patsubst %.pdf,%.png,$(wildcard *.pdf))

%.pdf: %.tex
	pdflatex -interaction=nonstopmode -synctex=1 $< || true

%.png: %.pdf
	mutool draw -r 400 -o $@ $<

clean:

full:
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	bibtex main
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	pdflatex -interaction=nonstopmode -halt-on-error main.tex

once:
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	
packages:
	tlmgr install pgf
	tlmgr install appendix
	tlmgr install tikz-qtree
	tlmgr install mdframed
	tlmgr install needspace
	tlmgr install enumitem
	tlmgr install breakcites
	tlmgr install algorithm2e
	tlmgr install ifoddpage
	tlmgr install relsize
	tlmgr install multirow

clean:
	rm -f *.aux sty/*.aux content/*.aux content/*/*.aux
	rm -f main.bbl main.blg main.idx main.lof main.lot main.toc main.log
	rm -f main.pdf

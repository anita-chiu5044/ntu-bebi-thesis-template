% BEBI adaptation of the NTU thesis template, 2026-09-26.
% Cover/metadata/layout adapted from ntuthesis.cls by Hsins (2020), as included
% in NTU-NCS-lab/NTU-Thesis-Writing-Template by Yen-Cheng Chu and contributors.
% MIT license: see LICENSE. Upstream ntuthesis.cls is retained for attribution.
% This class loads report directly; it never executes NCS style/submodule code.
\NeedsTeXFormat{LaTeX2e}[2020-10-01]
\ProvidesClass{bebi-thesis}[2026/09/26 v1.0 NTU BEBI thesis]
\RequirePackage{iftex}
\ifXeTeX\else
  \ClassError{bebi-thesis}{XeLaTeX is required}{Select XeLaTeX as the compiler.}
\fi
\RequirePackage{kvoptions}
\RequirePackage{etoolbox}
\SetupKeyvalOptions{family=bebi,prefix=bebi@}
\DeclareStringOption[draft]{mode}
\DeclareBoolOption[false]{print}
\DeclareBoolOption[false]{verification}
\DeclareBoolOption[true]{acknowledgements}
\DeclareStringOption[front/verification.pdf]{verificationfile}
\DeclareStringOption[figures/watermark.pdf]{watermarkfile}
\ProcessKeyvalOptions*
\edef\bebi@mode{\bebi@mode}
\newif\ifbebi@final
\ifdefstring{\bebi@mode}{final}{\bebi@finaltrue}{%
  \ifdefstring{\bebi@mode}{draft}{}{%
    \ClassError{bebi-thesis}{Unknown mode: \bebi@mode}{Use mode=draft or mode=final.}}}
\LoadClass[a4paper,12pt,oneside,openany]{report}
\RequirePackage{fontspec}
\RequirePackage{xeCJK}
\setmainfont{Times New Roman}[
  Path=fonts/english/,Extension=.ttf,
  BoldFont=*-Bold,ItalicFont=*-Italic,BoldItalicFont=*-BoldItalic]
\setCJKmainfont{BiauKai}[
  Path=fonts/chinese/,Extension=.ttf,BoldFont=Kaiti-Black]
\RequirePackage[top=3cm,bottom=2cm,left=3cm,right=3cm]{geometry}
\ifbebi@final\PassOptionsToPackage{monochrome}{xcolor}\fi
\RequirePackage{xcolor}
\RequirePackage{setspace}
\RequirePackage{graphicx}
\RequirePackage{tikz}
\RequirePackage{eso-pic}
\RequirePackage{pdfpages}
\RequirePackage{fancyhdr}
\RequirePackage{titlesec}
\RequirePackage{tocloft}
\RequirePackage{caption}
\RequirePackage{hyperref}
\RequirePackage[backend=biber,style=numeric,sorting=none]{biblatex}
\graphicspath{{figures/}}
\hypersetup{hidelinks,bookmarksnumbered=true}
\pdfstringdefDisableCommands{\def\thesisplaceholder#1{#1}}
\setlength{\parindent}{2em}
\setlength{\parskip}{0pt}
\XeTeXlinebreaklocale "zh"
\XeTeXlinebreakskip=0pt plus 1pt

% Centered page numbers throughout numbered front matter and body.
\pagestyle{fancy}
\fancyhf{}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\thepage}%
  \renewcommand{\headrulewidth}{0pt}\renewcommand{\footrulewidth}{0pt}}
\titleformat{\chapter}[display]{\normalfont\huge\bfseries\color{black}}%
  {\chaptertitlename\ \thechapter}{12pt}{\Huge}
\titlespacing*{\chapter}{0pt}{0pt}{24pt}
\titleformat{\section}{\normalfont\Large\bfseries\color{black}}{\thesection}{1em}{}
\captionsetup{font={small},labelfont=bf}
\setcounter{tocdepth}{2}
\renewcommand{\contentsname}{目次}
\renewcommand{\listfigurename}{圖次}
\renewcommand{\listtablename}{表次}
\renewcommand{\cfttoctitlefont}{\hfill\Large\bfseries}
\renewcommand{\cftaftertoctitle}{\hfill}
\renewcommand{\cftloftitlefont}{\hfill\Large\bfseries}
\renewcommand{\cftafterloftitle}{\hfill}
\renewcommand{\cftlottitlefont}{\hfill\Large\bfseries}
\renewcommand{\cftafterlottitle}{\hfill}
\setlength{\cftbeforetoctitleskip}{0pt}
\setlength{\cftbeforeloftitleskip}{0pt}
\setlength{\cftbeforelottitleskip}{0pt}

% Compatible metadata keys retain the upstream template's public interface.
\newcommand{\ntusetup}[1]{\setkeys{bebiinfo}{#1}}
\newcommand{\bebisetup}[1]{\setkeys{bebi}{#1}}
\newcommand{\bebi@metakey}[2]{%
  \expandafter\def\csname bebi@#2\endcsname{}%
  \define@key{bebiinfo}{#1}{\expandafter\def\csname bebi@#2\endcsname{##1}}}
\bebi@metakey{university}{university}
\bebi@metakey{university*}{universityen}
\bebi@metakey{college}{college}
\bebi@metakey{college*}{collegeen}
\bebi@metakey{institute}{institute}
\bebi@metakey{institute*}{instituteen}
\bebi@metakey{title}{title}
\bebi@metakey{title*}{titleen}
\bebi@metakey{author}{author}
\bebi@metakey{author*}{authoren}
\bebi@metakey{ID}{studentid}
\bebi@metakey{advisor}{advisor}
\bebi@metakey{advisor*}{advisoren}
\bebi@metakey{date}{date}
\bebi@metakey{oral-date}{oraldate}
\bebi@metakey{DOI}{doi}
\bebi@metakey{keywords}{keywords}
\bebi@metakey{keywords*}{keywordsen}

% Draft material stays visible. Final builds stop instead of silently dropping it.
\DeclareRobustCommand{\thesisplaceholder}[1]{%
  \ifbebi@final
    \ClassError{bebi-thesis}{Unresolved thesis placeholder}{Replace every thesisplaceholder before a final build.}%
  \else
    {\color{blue!65!black}[#1]}%
  \fi}
\DeclareRobustCommand{\todomark}[1]{\thesisplaceholder{TODO: #1}}

\ExplSyntaxOn
\cs_generate_variant:Nn \regex_match:nnTF {nV}
\cs_new_protected:Npn \bebi_validate_metadata: {
  \clist_map_inline:nn
    {university,universityen,college,collegeen,institute,instituteen,title,titleen,
     author,authoren,studentid,advisor,advisoren,date,doi,keywords,keywordsen} {
    \tl_set:Nv \l_tmpa_tl {bebi@##1}
    \tl_if_blank:VTF \l_tmpa_tl {
      \ClassError{bebi-thesis}{Required~metadata~is~empty:~##1}
        {Complete~ntusetup.tex~before~a~final~build.}
    } {
      \tl_set:Nx \l_tmpb_tl {\tl_to_str:V \l_tmpa_tl}
      \regex_match:nVTF {(?i)thesisplaceholder|todomark|TODO|PLACEHOLDER|XXXXX|待填} \l_tmpb_tl {
        \ClassError{bebi-thesis}{Unresolved~metadata~placeholder:~##1}
          {Replace~the~placeholder~with~approved~thesis~information.}
      } {}
    }
  }
  \tl_set:Nv \l_tmpa_tl {bebi@doi}
  \regex_match:nVTF {\A10\.[0-9]{4,9}/[^\s]+\Z} \l_tmpa_tl {} {
    \ClassError{bebi-thesis}{Invalid~or~missing~assigned~DOI}
      {Use~the~actual~assigned~10.xxxx/suffix~value,~without~a~URL~or~doi:~prefix.}
  }
  \tl_set:Nv \l_tmpa_tl {bebi@date}
  \regex_match:nVTF {\A[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])\Z} \l_tmpa_tl {} {
    \ClassError{bebi-thesis}{Thesis~date~must~be~YYYY-MM-DD}{Set~the~approved~thesis~date.}
  }
  \clist_map_inline:nn {keywords,keywordsen} {
    \clist_set:Nv \l_tmpa_clist {bebi@##1}
    \int_compare:nNnTF {\clist_count:N \l_tmpa_clist} < {5} {
      \ClassError{bebi-thesis}{At~least~5~keywords~required:~##1}{Provide~5--7~keywords~in~each~language.}
    } {
      \int_compare:nNnT {\clist_count:N \l_tmpa_clist} > {7} {
        \ClassError{bebi-thesis}{At~most~7~keywords~allowed:~##1}{Provide~5--7~keywords~in~each~language.}
      }
    }
  }
}
\cs_new_protected:Npn \bebi_date_zh: {
  \tl_set:Nv \l_tmpa_tl {bebi@date}
  \regex_match:nVTF {\A[0-9]{4}-[0-9]{2}-[0-9]{2}\Z} \l_tmpa_tl {
    \seq_set_split:NnV \l_tmpa_seq {-} \l_tmpa_tl
    中華民國~\int_eval:n {\seq_item:Nn \l_tmpa_seq {1}-1911}~年~
    \int_eval:n {\seq_item:Nn \l_tmpa_seq {2}}~月
  } {\thesisplaceholder{論文年月}}
}
\cs_new_protected:Npn \bebi_date_en: {
  \tl_set:Nv \l_tmpa_tl {bebi@date}
  \regex_match:nVTF {\A[0-9]{4}-[0-9]{2}-[0-9]{2}\Z} \l_tmpa_tl {
    \seq_set_split:NnV \l_tmpa_seq {-} \l_tmpa_tl
    \clist_item:nn {January,February,March,April,May,June,July,August,September,October,November,December}
      {\seq_item:Nn \l_tmpa_seq {2}}~\seq_item:Nn \l_tmpa_seq {1}
  } {\thesisplaceholder{Thesis~month~and~year}}
}
\cs_new_protected:Npn \bebi_keywords:nn #1#2 {
  \clist_set:Nv \l_tmpa_clist {bebi@#1}
  \clist_use:Nn \l_tmpa_clist {#2}
}
\cs_new_eq:NN \bebi@validatedata \bebi_validate_metadata:
\cs_new_eq:NN \bebi@datezh \bebi_date_zh:
\cs_new_eq:NN \bebi@dateen \bebi_date_en:
\cs_new_eq:NN \bebi@keywordsdisplay \bebi_keywords:nn
\ExplSyntaxOff

\AtBeginDocument{%
  \color{black}%
  \ifbebi@final
    \bebi@validatedata
    \IfFileExists{\bebi@watermarkfile}{}{%
      \ClassError{bebi-thesis}{Official NTU watermark file missing}{Download the official library watermark and set watermarkfile.}}
    \ifbebi@print\ifbebi@verification\else
      \ClassError{bebi-thesis}{Final paper copy requires the signed verification letter}{Set verification=true and supply the actual signed PDF.}
    \fi\fi
  \fi
  \ifbebi@verification
    \IfFileExists{\bebi@verificationfile}{}{%
      \ClassError{bebi-thesis}{Verification PDF missing}{Supply the signed PDF or set verification=false for the electronic copy.}}
  \fi
}

% Library instructions: official image at 50% scale/opacity; top/right 2.5cm.
% DOI at 12pt, right/bottom 1cm. No overlays on signed verification pages.
\newif\ifbebi@overlays
\bebi@overlaystrue
\newif\ifbebi@outercover
\bebi@outercovertrue
% Register XeTeX/PGF transparency resources before the first page ships.
% Creating opacity for the first time inside shipout leaves page 1 without
% the ExtGState resource, so cache the image before any cover is rendered.
\newsavebox{\bebi@watermarkbox}
\AtBeginDocument{%
  \ifbebi@final
    \sbox{\bebi@watermarkbox}{%
      \begin{tikzpicture}
        \node[inner sep=0pt,outer sep=0pt,opacity=0.5]
          {\includegraphics[scale=0.5]{\bebi@watermarkfile}};
      \end{tikzpicture}}%
  \fi}
\AddToShipoutPictureBG{%
  \ifbebi@final\ifbebi@overlays
    \begin{tikzpicture}[remember picture,overlay]
      \node[anchor=north east,inner sep=0pt,outer sep=0pt]
        at ([xshift=-2.5cm,yshift=-2.5cm]current page.north east)
        {\usebox{\bebi@watermarkbox}};
    \end{tikzpicture}%
  \fi\fi}
\AddToShipoutPictureBG{%
  \ifbebi@final\ifbebi@overlays
    \begin{tikzpicture}[remember picture,overlay]
      \node[anchor=south east,inner sep=0pt,outer sep=0pt,text=black]
        at ([xshift=-1cm,yshift=1cm]current page.south east)
        {\fontsize{12}{12}\selectfont doi:\bebi@doi};
    \end{tikzpicture}%
  \fi\fi}

% Cover adaptation: explicit short lines accommodate BEBI's long name.
\newcommand{\makecover}{%
  \clearpage\hypersetup{pageanchor=false}%
  \ifbebi@print\ifbebi@outercover\bebi@overlaysfalse\fi\fi
  \newgeometry{top=4cm,bottom=3cm,left=3cm,right=3cm}%
  \begin{titlepage}\singlespacing\centering
    \fontsize{18}{27}\selectfont
    \bebi@university\bebi@college\par
    \bebi@institute\par
    碩士論文\ifbebi@final\else （初稿）\fi\par
    \medskip\fontsize{14}{21}\selectfont
    \bebi@instituteen\par
    \bebi@collegeen\par
    \fontsize{16}{24}\selectfont
    \bebi@universityen\par
    Master's Thesis\ifbebi@final\else\ (Draft)\fi\par
    \vfill\fontsize{18}{27}\selectfont
    \bebi@title\par\bebi@titleen\par
    \vfill
    \bebi@author\par\bebi@authoren\par
    \vfill
    指導教授：\bebi@advisor\par
    Advisor: \bebi@advisoren\par
    \vfill
    \bebi@datezh\par\bebi@dateen\par
  \end{titlepage}%
  \clearpage\bebi@overlaystrue\bebi@outercoverfalse\restoregeometry}
\newcommand{\makepapertitlepage}{\ifbebi@print\makecover\fi}

% Start Roman i exactly once, after all unnumbered cover/title pages.
\newcommand{\frontmatter}{%
  \clearpage\pagenumbering{roman}\hypersetup{pageanchor=true}%
  \pagestyle{fancy}\onehalfspacing}
\newcommand{\includeverification}{%
  \ifbebi@verification
    \clearpage\bebi@overlaysfalse
    \includepdf[pages=-,pagecommand={\thispagestyle{plain}},
      pagecommand*={\phantomsection
        \addcontentsline{toc}{chapter}{口試委員審定書}
        \label{bebi:verification}}]{\bebi@verificationfile}%
    \clearpage\bebi@overlaystrue
  \fi}
\newcommand{\makeacknowledgements}{%
  \ifbebi@acknowledgements\include{front/acknowledgement}\fi}
\newcommand{\bebi@frontheading}[1]{%
  \chapter*{\centering #1}\phantomsection\addcontentsline{toc}{chapter}{#1}}
\newenvironment{acknowledgement}{\bebi@frontheading{誌謝}}{\par}
\renewenvironment{abstract}{%
  \bebi@frontheading{摘要}\onehalfspacing
  {\centering\large\bfseries\bebi@title\par}\medskip
}{%
  \par\bigskip\noindent\textbf{關鍵字：}%
  \bebi@keywordsdisplay{keywords}{、}\par\clearpage}
\newenvironment{abstract*}{%
  \bebi@frontheading{ABSTRACT}\doublespacing
  {\centering\large\bfseries\bebi@titleen\par}\medskip
}{%
  \par\bigskip\noindent\textbf{Keywords: }%
  \bebi@keywordsdisplay{keywordsen}{, }\par\clearpage}
\newcommand{\maketableofcontents}{%
  \clearpage\begingroup\singlespacing
  \phantomsection\addcontentsline{toc}{chapter}{目次}\tableofcontents
  \clearpage\endgroup}
\newcommand{\makelistoffigures}{%
  \clearpage\begingroup\singlespacing
  \phantomsection\addcontentsline{toc}{chapter}{圖次}\listoffigures
  \clearpage\endgroup}
\newcommand{\makelistoftables}{%
  \clearpage\begingroup\singlespacing
  \phantomsection\addcontentsline{toc}{chapter}{表次}\listoftables
  \clearpage\endgroup}
\newcommand{\mainmatter}{%
  \clearpage\pagenumbering{arabic}\setcounter{chapter}{0}%
  \normalfont\normalsize\doublespacing}
% setspace alone controls English body spacing. Do not stack a custom 12/18
% font baseline with another stretch factor. Captions/footnotes follow setspace.
\endinput

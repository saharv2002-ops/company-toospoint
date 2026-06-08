%% proposal.cls — Personal consulting proposal class for Sahar Feiz
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{proposal}[2026/01/01 Personal Consulting Proposal Class]

\LoadClass[11pt,letterpaper]{article}

%% ─── Packages ───────────────────────────────────────────────────────────────
\RequirePackage[
  top=1.1in, bottom=1.1in,
  left=1.25in, right=1.25in,
  headheight=60pt,
  headsep=24pt,
  footskip=36pt
]{geometry}
\RequirePackage{fontspec}
\RequirePackage{xcolor}
\RequirePackage{graphicx}
\RequirePackage{fancyhdr}
\RequirePackage{titlesec}
\RequirePackage{enumitem}
\RequirePackage{array}
\RequirePackage{booktabs}
\RequirePackage{tabularx}
\RequirePackage{microtype}
\RequirePackage{setspace}
\RequirePackage{parskip}
\RequirePackage{lastpage}
\RequirePackage{hyperref}
\RequirePackage{mdframed}
\RequirePackage{tikz}
\RequirePackage{eso-pic}

%% ─── Colour Palette ─────────────────────────────────────────────────────────
\definecolor{TPOrange}{HTML}{F08A5D}
\definecolor{TPTeal}{HTML}{2A9D8F}
\definecolor{TPDark}{HTML}{1A1A2E}
\definecolor{TPGray}{HTML}{6B7280}
\definecolor{TPLight}{HTML}{F9FAFB}
\definecolor{TPBorder}{HTML}{E5E7EB}
\definecolor{TPAccent}{HTML}{E76F51}

%% ─── Fonts ──────────────────────────────────────────────────────────────────
\IfFontExistsTF{TeX Gyre Termes}{%
  \setmainfont{TeX Gyre Termes}%
}{%
  \setmainfont{Times New Roman}%
}
\IfFontExistsTF{TeX Gyre Heros}{%
  \setsansfont{TeX Gyre Heros}%
}{%
  \setsansfont{Helvetica Neue}%
}

%% ─── Hyperref ───────────────────────────────────────────────────────────────
\hypersetup{
  colorlinks=false,
  pdfborder={0 0 0},
  pdftitle={Consulting Proposal},
  pdfauthor={Sahar Feiz}
}

%% ─── Section Styling ────────────────────────────────────────────────────────
\titleformat{\section}
  {\sffamily\bfseries\large\color{TPDark}}
  {\textcolor{TPTeal}{\thesection.}}
  {0.6em}
  {}
  [\vspace{2pt}{\color{TPOrange}\rule{\linewidth}{1.5pt}}\vspace{2pt}]

\titlespacing*{\section}{0pt}{18pt}{8pt}

\titleformat{\subsection}
  {\sffamily\bfseries\normalsize\color{TPTeal}}
  {}{0pt}{}

\titlespacing*{\subsection}{0pt}{10pt}{4pt}

%% ─── Header / Footer ────────────────────────────────────────────────────────
\pagestyle{fancy}
\fancyhf{}

\fancyhead[L]{%
  \sffamily\footnotesize\color{TPGray}%
  \textbf{\color{TPDark}\MakeUppercase{Sahar Feiz}}\\[2pt]
  Independent Consultant%
}
\fancyhead[C]{%
  \sffamily\small\color{TPGray}%
  \textbf{\color{TPDark}CONSULTING PROPOSAL}\\[2pt]
  \textcolor{TPTeal}{Prepared for One World Global}%
}
\fancyhead[R]{%
  \sffamily\footnotesize\color{TPGray}%
  \textbf{\color{TPAccent}CONFIDENTIAL}\\[2pt]
  \today%
}

\renewcommand{\headrulewidth}{0pt}
\renewcommand{\headrule}{%
  \begin{tikzpicture}
    \fill[TPOrange] (0,0) rectangle (0.5\headwidth, 2pt);
    \fill[TPTeal]   (0.5\headwidth,0) rectangle (\headwidth, 2pt);
  \end{tikzpicture}%
}

\fancyfoot[L]{\sffamily\footnotesize\color{TPGray}Sahar Feiz\enspace·\enspace Confidential}
\fancyfoot[C]{%
  \begin{tikzpicture}
    \fill[TPOrange] (0,0) rectangle (0.09\textwidth,1.2pt);
    \fill[TPTeal]   (0.09\textwidth,0) rectangle (0.18\textwidth,1.2pt);
  \end{tikzpicture}%
}
\fancyfoot[R]{\sffamily\footnotesize\color{TPGray}Page \thepage\ of \pageref{LastPage}}

%% ─── Cover / Title Block ─────────────────────────────────────────────────────
\newcommand{\proposaltitle}[4]{%
  % #1 doc type  #2 prepared for  #3 prepared by  #4 effective date
  \thispagestyle{empty}
  \AddToShipoutPictureBG*{%
    \AtPageLowerLeft{%
      \begin{tikzpicture}[remember picture,overlay]
        \fill[TPTeal!8] (0,0) rectangle (\paperwidth,\paperheight);
        \fill[white]    (1cm,1cm) rectangle (\paperwidth-1cm,\paperheight-1cm);
        % top accent bar
        \fill[TPOrange] (1cm,\paperheight-1cm) rectangle (\paperwidth/2,\paperheight-1cm+8pt);
        \fill[TPTeal]   (\paperwidth/2,\paperheight-1cm) rectangle (\paperwidth-1cm,\paperheight-1cm+8pt);
        % bottom accent bar
        \fill[TPOrange] (1cm,1cm) rectangle (\paperwidth/2,1cm+5pt);
        \fill[TPTeal]   (\paperwidth/2,1cm) rectangle (\paperwidth-1cm,1cm+5pt);
      \end{tikzpicture}%
    }%
  }%
  \vspace*{3.0cm}
  \begin{center}
    {\sffamily\fontsize{10}{12}\selectfont\color{TPGray}\MakeUppercase{Independent Consulting Proposal}}\\[16pt]
    {\color{TPBorder}\rule{0.45\textwidth}{0.5pt}}\\[26pt]
    {\sffamily\bfseries\fontsize{40}{44}\selectfont\color{TPDark}SAHAR FEIZ}\\[10pt]
    {\sffamily\fontsize{10}{12}\selectfont\color{TPTeal}\MakeUppercase{Operational \& Growth Consulting}}\\[28pt]
    {\color{TPBorder}\rule{0.45\textwidth}{0.5pt}}\\[26pt]
    {\sffamily\bfseries\fontsize{22}{26}\selectfont\color{TPDark}#1}\\[8pt]
    {\sffamily\large\color{TPTeal}Prepared for #2}\\[28pt]
    \begin{mdframed}[
      linecolor=TPBorder,
      linewidth=1pt,
      roundcorner=6pt,
      backgroundcolor=TPLight,
      innerleftmargin=24pt,
      innerrightmargin=24pt,
      innertopmargin=16pt,
      innerbottommargin=16pt,
      leftmargin=2cm,
      rightmargin=2cm
    ]
      \sffamily\small
      \begin{tabular}{@{}ll@{}}
        \textcolor{TPGray}{Prepared By:}      & \textbf{#3} \\[4pt]
        \textcolor{TPGray}{Proposed Start:}   & \textbf{#4} \\[4pt]
        \textcolor{TPGray}{Document Type:}    & \textbf{Consulting Proposal} \\[4pt]
        \textcolor{TPGray}{Classification:}   & \textbf{\textcolor{TPAccent}{Confidential}} \\
      \end{tabular}
    \end{mdframed}
  \end{center}
  \clearpage
  \setcounter{page}{1}
}

%% ─── Signature Block ─────────────────────────────────────────────────────────
\newcommand{\signatureblock}[2]{%
  \vspace{6pt}
  \begin{minipage}[t]{0.44\textwidth}
    \sffamily\small
    {\color{TPGray}Authorized Signature}\\[24pt]
    \begin{tikzpicture}
      \draw[TPDark,line width=0.8pt] (0,0) -- (6cm,0);
    \end{tikzpicture}\\[4pt]
    \textbf{#1}\\
    \textcolor{TPGray}{#2}\\[10pt]
    {\color{TPGray}Printed Name}\\[16pt]
    \begin{tikzpicture}
      \draw[TPBorder,line width=0.8pt] (0,0) -- (6cm,0);
    \end{tikzpicture}\\[10pt]
    {\color{TPGray}Date}\\[16pt]
    \begin{tikzpicture}
      \draw[TPBorder,line width=0.8pt] (0,0) -- (6cm,0);
    \end{tikzpicture}
  \end{minipage}%
}

%% ─── Callout Box ─────────────────────────────────────────────────────────────
\newmdenv[
  linecolor=TPTeal,
  linewidth=1.5pt,
  topline=false, rightline=false, bottomline=false,
  backgroundcolor=TPLight,
  innerleftmargin=14pt,
  innertopmargin=8pt,
  innerbottommargin=8pt,
  skipabove=6pt,
  skipbelow=6pt
]{clausebox}

%% ─── Pillar Card ─────────────────────────────────────────────────────────────
\newcommand{\pillar}[2]{%
  \begin{mdframed}[
    linecolor=TPOrange,
    linewidth=2pt,
    topline=false, rightline=false, bottomline=false,
    backgroundcolor=white,
    innerleftmargin=12pt,
    innertopmargin=6pt,
    innerbottommargin=6pt,
    skipabove=4pt,
    skipbelow=4pt
  ]
    \sffamily\bfseries\color{TPDark}#1\\[1pt]
    \sffamily\footnotesize\color{TPGray}#2
  \end{mdframed}%
}

\endinput

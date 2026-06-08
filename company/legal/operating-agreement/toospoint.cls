%% toospoint.cls — Professional consulting contract class
%% Fortune 500-grade document design for ToosPoint Consulting
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{toospoint}[2024/01/01 ToosPoint Contract Class]

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

%% ─── Brand Colours ──────────────────────────────────────────────────────────
\definecolor{TPOrange}{HTML}{F08A5D}
\definecolor{TPTeal}{HTML}{2A9D8F}
\definecolor{TPDark}{HTML}{1A1A2E}
\definecolor{TPGray}{HTML}{6B7280}
\definecolor{TPLight}{HTML}{F9FAFB}
\definecolor{TPBorder}{HTML}{E5E7EB}
\definecolor{TPAccent}{HTML}{E76F51}

%% ─── Fonts ──────────────────────────────────────────────────────────────────
\setmainfont{texgyretermes}[
  Extension=.otf,
  UprightFont=*-regular,
  BoldFont=*-bold,
  ItalicFont=*-italic,
  BoldItalicFont=*-bolditalic
]
\setsansfont{texgyreheros}[
  Extension=.otf,
  UprightFont=*-regular,
  BoldFont=*-bold,
  ItalicFont=*-italic,
  BoldItalicFont=*-bolditalic
]

%% ─── Hyperref ───────────────────────────────────────────────────────────────
\hypersetup{
  colorlinks=false,
  pdfborder={0 0 0},
  pdftitle={Consulting Agreement},
  pdfauthor={ToosPoint Consulting}
}

%% ─── Section Styling ────────────────────────────────────────────────────────
\titleformat{\section}
  {\sffamily\bfseries\large\color{TPDark}}
  {\textcolor{TPTeal}{\thesection.}}
  {0.6em}
  {}
  [\vspace{2pt}{\color{TPOrange}\rule{\linewidth}{1.5pt}}\vspace{2pt}]

\titlespacing*{\section}{0pt}{18pt}{8pt}

%% ─── Header / Footer ────────────────────────────────────────────────────────
\pagestyle{fancy}
\fancyhf{}

\fancyhead[L]{%
  \includegraphics[height=38pt]{toospoint-logo}%
}
\fancyhead[C]{%
  \sffamily\small\color{TPGray}%
  \textbf{\color{TPDark}CONSULTING AGREEMENT}\\[2pt]
  \textcolor{TPTeal}{ToosPoint Consulting}\;\textcolor{TPGray}{×}\;Simplified Group BPO LLC%
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

\fancyfoot[L]{\sffamily\footnotesize\color{TPGray}ToosPoint Consulting\enspace·\enspace Confidential}
\fancyfoot[C]{%
  \begin{tikzpicture}
    \fill[TPOrange] (0,0) rectangle (0.09\textwidth,1.2pt);
    \fill[TPTeal]   (0.09\textwidth,0) rectangle (0.18\textwidth,1.2pt);
  \end{tikzpicture}%
}
\fancyfoot[R]{\sffamily\footnotesize\color{TPGray}Page \thepage\ of \pageref{LastPage}}

%% ─── Cover / Title Block ─────────────────────────────────────────────────────
\newcommand{\contracttitle}[3]{%
  % #1 doc type  #2 parties  #3 effective date
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
  \vspace*{1.8cm}
  \begin{center}
    \includegraphics[height=72pt]{toospoint-logo}\\[20pt]
    {\sffamily\fontsize{9}{11}\selectfont\color{TPGray}\MakeUppercase{ToosPoint Consulting}}\\[6pt]
    {\color{TPBorder}\rule{0.35\textwidth}{0.5pt}}\\[18pt]
    {\sffamily\bfseries\fontsize{26}{30}\selectfont\color{TPDark}#1}\\[12pt]
    {\sffamily\large\color{TPTeal}#2}\\[32pt]
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
        \textcolor{TPGray}{Effective Date:}   & \textbf{#3} \\[4pt]
        \textcolor{TPGray}{Document Type:}    & \textbf{Operating Agreement} \\[4pt]
        \textcolor{TPGray}{Classification:}   & \textbf{\textcolor{TPAccent}{Confidential}} \\
      \end{tabular}
    \end{mdframed}
    \vspace{24pt}
    {\color{TPBorder}\rule{0.5\textwidth}{0.5pt}}
  \end{center}
  \clearpage
  \setcounter{page}{1}
}

%% ─── Signature Block ─────────────────────────────────────────────────────────
\newcommand{\signatureblock}[2]{%
  % #1 party name  #2 title
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

%% ─── Clause Box ──────────────────────────────────────────────────────────────
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

\endinput

%% toospoint-invoice.cls — ToosPoint Consulting branded invoice
%% Mirrors the brand identity of toospoint.cls (logo, colors, accent bars,
%% fonts) but tailored to a single-page invoice layout.
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{toospoint-invoice}[2026/05/07 ToosPoint Invoice Class]

\LoadClass[11pt,letterpaper]{article}

%% ─── Packages ───────────────────────────────────────────────────────────────
\RequirePackage[
  top=1.05in, bottom=0.9in,
  left=0.9in, right=0.9in,
  headheight=56pt,
  headsep=18pt,
  footskip=28pt
]{geometry}
\RequirePackage{fontspec}
\RequirePackage{xcolor}
\RequirePackage{colortbl}
\RequirePackage{graphicx}
\RequirePackage{fancyhdr}
\RequirePackage{enumitem}
\RequirePackage{array}
\RequirePackage{tabularx}
\RequirePackage{microtype}
\RequirePackage{parskip}
\RequirePackage{lastpage}
\RequirePackage{hyperref}
\RequirePackage{mdframed}
\RequirePackage{tikz}
\RequirePackage{ragged2e}
\RequirePackage{fontawesome5}
\RequirePackage{etoolbox}

%% ─── Brand Colours (identical to toospoint.cls) ─────────────────────────────
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
  pdftitle={Invoice},
  pdfauthor={ToosPoint Consulting}
}

%% ─── Invoice metadata commands (set in the document) ────────────────────────
\newcommand{\invoiceno}[1]{\def\@invoiceno{#1}}
\newcommand{\invoiceclient}[1]{\def\@invoiceclient{#1}}
\newcommand{\invoicedate}[1]{\def\@invoicedate{#1}}
\invoiceno{}\invoiceclient{}\invoicedate{\today}

%% ─── Header / Footer ────────────────────────────────────────────────────────
\pagestyle{fancy}
\fancyhf{}

\fancyhead[L]{%
  \includegraphics[height=38pt]{toospoint-logo}%
}
\fancyhead[C]{%
  \sffamily\small\color{TPGray}%
  \textbf{\color{TPDark}INVOICE}\\[2pt]
  \textcolor{TPTeal}{ToosPoint Consulting}\;\textcolor{TPGray}{×}\;\@invoiceclient%
}
\fancyhead[R]{%
  \sffamily\footnotesize\color{TPGray}%
  \textbf{\color{TPAccent}INVOICE \#\@invoiceno}\\[2pt]
  \@invoicedate%
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

%% ─── Helper: small uppercase eyebrow label ──────────────────────────────────
\newcommand{\tpeyebrow}[1]{%
  \sffamily\fontsize{8}{10}\selectfont\textbf{\textcolor{TPGray}{\MakeUppercase{#1}}}%
}

%% ─── Invoice title block (top of body) ──────────────────────────────────────
%% Usage: \invoicetitle
\newcommand{\invoicetitle}{%
  \vspace*{4pt}
  \begin{tabularx}{\textwidth}{@{}X r@{}}
    {\sffamily\bfseries\fontsize{34}{38}\selectfont\color{TPDark}Invoice}
    &
    \begin{tabular}{r}
      {\tpeyebrow{Invoice No.}}\\[2pt]
      {\sffamily\fontsize{14}{16}\selectfont\textbf{\color{TPDark}\@invoiceno}}
    \end{tabular}
  \end{tabularx}
  \vspace{4pt}\par
  \begin{tikzpicture}
    \fill[TPOrange] (0,0) rectangle (0.5\textwidth, 1.4pt);
    \fill[TPTeal]   (0.5\textwidth,0) rectangle (\textwidth, 1.4pt);
  \end{tikzpicture}\par
  \vspace{2pt}
  {\color{TPBorder}\rule{\textwidth}{0.4pt}}\par
  \vspace{0.4cm}
}

%% ─── Meta block: Issued / Due / Terms / Service Period ──────────────────────
%% Usage: \invoicemeta{issued}{due}{terms}{service period}
\newcommand{\invoicemeta}[4]{%
  \vspace*{0.4cm}
  \renewcommand{\arraystretch}{1.35}
  \begin{tabularx}{\textwidth}{@{} X r @{}}
    \tpeyebrow{Issued} & \sffamily\color{TPDark} #1 \\
    \tpeyebrow{Payment Due} & \sffamily\color{TPDark}\textbf{#2} \\
    \tpeyebrow{Payment Terms} & \sffamily\color{TPDark} #3 \\
    \tpeyebrow{Service Period} & \sffamily\color{TPDark} #4 \\
  \end{tabularx}
  \renewcommand{\arraystretch}{1.2}
  \vspace{0.4cm}
}

%% ─── From / Billed To block ─────────────────────────────────────────────────
%% Usage: \invoiceparties{from-block}{billed-to-block}
%% Each block uses tight line spacing (parskip=0). Top-aligned columns.
\newcommand{\invoiceparties}[2]{%
  \noindent
  \begin{minipage}[t]{0.5\textwidth}
    \tpeyebrow{From}\par\vspace{4pt}
    {\setlength{\parskip}{0pt}\sffamily\color{TPDark}#1\par}
  \end{minipage}%
  \begin{minipage}[t]{0.5\textwidth}
    \tpeyebrow{Billed To}\par\vspace{4pt}
    {\setlength{\parskip}{0pt}\sffamily\color{TPDark}#2\par}
  \end{minipage}\par
  \vspace{0.5cm}
}

%% ─── Line items table ───────────────────────────────────────────────────────
%% Usage: \invoicelines{ <row1> <row2> ... } — rows built with \invoiceline
\newcommand{\invoicelines}[1]{%
  \tpeyebrow{Description of Services}\par
  \vspace{6pt}
  \renewcommand{\arraystretch}{1.5}
  \arrayrulecolor{TPBorder}
  \begin{tabularx}{\textwidth}{@{} >{\RaggedRight}X r r @{}}
    \hline
    \rowcolor{TPLight}
    {\tpeyebrow{Description}} &
    {\tpeyebrow{Rate}} &
    {\tpeyebrow{Amount}} \\
    \hline
    #1
    \hline
  \end{tabularx}
  \renewcommand{\arraystretch}{1.2}
  \vspace{0.25cm}
}

%% Single line item row: \invoiceline{description}{subtext}{rate}{amount}
\newcommand{\invoiceline}[4]{%
  \sffamily\textbf{\color{TPDark}#1}\newline
  \sffamily\footnotesize\color{TPGray}#2
  & \sffamily\color{TPDark}#3
  & \sffamily\color{TPDark}#4 \\
}

%% ─── Totals block (right-aligned) ───────────────────────────────────────────
%% Usage: \invoicetotals{subtotal}{tax}{total label}{total amount}
\newcommand{\invoicetotals}[4]{%
  \hfill
  \begin{minipage}{0.5\textwidth}
    \renewcommand{\arraystretch}{1.35}
    \arrayrulecolor{TPBorder}
    \begin{tabularx}{\textwidth}{@{} X r @{}}
      \sffamily\color{TPGray}Subtotal & \sffamily\color{TPDark}#1 \\
      \sffamily\color{TPGray}Tax & \sffamily\color{TPDark}#2 \\
      \hline
      \rowcolor{TPLight}
      \sffamily\textbf{\color{TPDark}#3} &
      {\sffamily\fontsize{16}{18}\selectfont\textbf{\color{TPDark}#4}} \\
      \hline
    \end{tabularx}
  \end{minipage}\par
  \vspace{0.6cm}
}

%% ─── Payment instructions block ─────────────────────────────────────────────
%% Usage: \invoicepayment{method}{detail}{reference note}
%% The reference note is optional — pass {} to omit it.
\newcommand{\invoicepayment}[3]{%
  \begin{mdframed}[
    linecolor=TPTeal,
    linewidth=1.5pt,
    topline=false, rightline=false, bottomline=false,
    backgroundcolor=TPLight,
    innerleftmargin=14pt,
    innertopmargin=10pt,
    innerbottommargin=10pt,
    skipabove=4pt,
    skipbelow=4pt
  ]
    \tpeyebrow{Payment Method}\par
    \vspace{4pt}
    {\sffamily\textbf{\color{TPDark}#1}} \quad\textcolor{TPGray}{$\to$}\quad
    {\sffamily\textbf{\color{TPTeal}#2}}%
    \notblank{#3}{\par\vspace{2pt}{\sffamily\footnotesize\color{TPGray}#3}}{}%
  \end{mdframed}
}

\endinput

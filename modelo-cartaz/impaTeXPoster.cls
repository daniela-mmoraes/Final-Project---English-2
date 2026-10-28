\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{impaTeXPoster}[2026/05/21 My Custom LaTeX Class]

% ==================================================
% 1. EARLY PACKAGES
% ==================================================
\RequirePackage{kvoptions}
\RequirePackage{ifthen}

\DeclareVoidOption*{
    \PassOptionsToClass{\CurrentOption}{tikzposter}
}

% ==================================================
% 2. OPTIONS SYSTEM
% ==================================================
\SetupKeyvalOptions{
    family=impa,
    prefix=impa@
}

\DeclareStringOption[basic]{palette}
\DeclareStringOption[light]{mode}

\ProcessKeyvalOptions*

% ==================================================
% 3. LOAD BASE CLASS
% ==================================================
\LoadClass[a0paper,portrait]{tikzposter}

% ==================================================
% 4. TYPOGRAPHY
% ==================================================
% Nova opção de fonte: Helvetica (sans-serif)
\RequirePackage[scaled=0.92]{helvet} 
\renewcommand{\familydefault}{\sfdefault}

% Tamanho padrão da fonte
\renewcommand{\normalsize}{%
    \fontsize{28}{36}\selectfont
}

% ABNT NBR 14724 §5.3: recuo de 1,25 cm na primeira linha
% Em pôster, é aceitável trocar por espaço entre parágrafos
% (mais legível). Escolhemos espaço entre parágrafos sem recuo,
% pois é o ultilizado em pôsteres científicos.
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.6em}

% ==================================================
% 5. METADATA 
% ==================================================
% Logo esquerda
\newcommand{\rightposterlogo}[1]{\def\impa@rightlogo{#1}}
\def\impa@rightlogo{}

% Logo direita
\newcommand{\posterlogo}[1]{\def\impa@leftlogo{#1}}
\def\impa@leftlogo{}

% Autores e emails
\renewcommand{\author}[1]{\def\impa@authors{#1}}
\newcommand{\authoremail}[1]{\def\impa@emails{#1}}
\def\impa@authors{}
\def\impa@emails{}

% Subtítulo
\newcommand{\subtitle}[1]{\def\impa@subtitle{#1}}
\def\impa@subtitle{}

% ==================================================
% 6. LOAD MODULES
% ==================================================
\RequirePackage{impaTechColors} % Definição das cores oficiais do ImpaTech
\RequirePackage{impaTexThemes} % Definição de temas da classe
\RequirePackage{impaTeXLayout} % Definição do layout do poster (cabeçalho, colunas, etc.)
\RequirePackage{impaTexSettings} % Definição de comandos de personalização globais
\RequirePackage{impaTexComponents} % Definição dos ambientes personalisados (blocos de texto, referências, legendas, etc.)

\endinput

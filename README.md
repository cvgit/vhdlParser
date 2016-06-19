# vhdlParser

So far the only thing this parser does is take in a file, and generate a tree with all identifiers and Lexer Rules. All information is extracted from VHDL and can be printed to stdout. The only part missing are the functions to group the information.

The reasons to share my project at this early stage are:
- I trust in the cloud for input :)
- I didn't find any free useful SW during my quest
- During my quest I noticed people to be looking for SW to extract port lists, unused signals, dependencies, etc
- I found some people that gave up doing this because 1) starting from scratch is too hard and 2) tools to help might seem overwhelmingly complicated at first
- and ... I'm curious about how this goes.

First, how to get this running?
- Read http://www.antlr.org/download/, i.e.:
  - Get: http://www.antlr.org/download/antlr-4.5.3-complete.jar
  - Run: pip install antlr4-python3-runtime
- Make sure you have Java installed (>1.7 i believe)
- Get the grammar: https://github.com/antlr/grammars-v4/blob/master/vhdl/vhdl.g4
- Run: java -jar antlr-4.5.3-complete.jar -visitor -Dlanguage=Python3 -package vhdl -o vhdl vhdl.g4
  - this assumes java to be in $PATH
  - antlr-4.5.3-compete.jar to be in current directory
  - grammar vhdl.g4 to be in current directory
  - and generates Python3 backend
  - consisting of vhdlLexer, vhdlParser, vhdlListerner
  - also creates a visitor which we don't need
  - and puts all this stuff in vhdl/

I should thank the person who wrote a grammar for VHDL, see:
https://github.com/antlr/grammars-v4

I should also tank the person/people developing ANTLR, see:
http://www.antlr.org/

ANTLR uses that grammar to generate a lexer, which translates some input VHDL file into a list of tokens. So you don't need to write 1000s of tricky regexps yourself. It also generates a parser which reads the tokens and a listener that triggers functions like enter_Library_clause(self, ctx), exit_Library_clause(self,ctx) or enter_Identifier(self, ctx) and exit_Identifier(self, ctx). Oh, that's right, I chose to rely on the Python flavor of ANTLR.

Besides trying to get ANTLR running and understand the basics, I wrote a generic class that overrides these enter_ and exit_ methods to generate a tree data structure along with a print function. The leafs of the trees are the Identifiers, the text of which is obviously also stored. Language keywords are not stored to date, though that would merely take minutes to add if necessary.
